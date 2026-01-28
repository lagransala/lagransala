import calendar
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import contains_eager, selectinload
from sqlmodel import Session, select

from lagransala.schedule.domain import Event, EventDateTime, Venue
from lagransala.shared.infrastructure.initialize_sqlmodel import initialize_sqlmodel

# --- Configuration ---
# Assumes the database file is in the project root.
# Adjust the path if your database is located elsewhere.
DATABASE_URL = "sqlite:///lagransala.db"
if not Path("lagransala.db").exists():
    # A fallback for when the script is run from within the applications/web directory
    DATABASE_URL = "sqlite:///../../../lagransala.db"


# --- FastAPI Application Setup ---
app = FastAPI(
    title="La Gran Sala - Event Schedule",
    description="Web application to display the event schedule.",
)

# Setup Jinja2 templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=templates_path)

SPANISH_MONTHS = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

SPANISH_WEEKDAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


def format_date_spanish(date_str: str) -> str:
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = SPANISH_WEEKDAYS[date_obj.weekday()]
        month_name = SPANISH_MONTHS[date_obj.month - 1]
        return f"{day_name} {date_obj.day} de {month_name}"
    except (ValueError, IndexError):
        return date_str


def url_domain(url: str) -> str:
    return urlparse(str(url)).netloc


templates.env.globals["format_date_spanish"] = format_date_spanish
templates.env.filters["url_domain"] = url_domain


# --- Database Setup ---
engine = initialize_sqlmodel(DATABASE_URL)


def get_session():
    """Dependency to get a database session."""
    with Session(engine) as session:
        yield session


def event_query(
    session: Session, start: datetime, end: datetime, venue: Venue | None = None
) -> Iterable[Event]:
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    query = (
        select(Event)
        .join(Event.schedule)  # type: ignore
        .options(contains_eager(Event.schedule), selectinload(Event.venue))  # type: ignore
        .where(EventDateTime.datetime >= start)
        .where(EventDateTime.datetime <= end)
        .distinct()
    )

    if venue:
        query = query.where(Event.venue_id == venue.id)

    return session.exec(query).unique().all()


def month_events(session: Session, month: int, year: int):
    _, num_days = calendar.monthrange(year, month)
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, num_days)
    return event_query(session, start_date, end_date)


def day_events(session: Session, day: int, month: int, year: int):
    start = datetime(year, month, day)
    return event_query(session, start, start)


def generate_event_list_data(events: Iterable[Event]) -> dict:
    """
    Generates a dictionary of events grouped by date and time.
    """
    events_by_date = defaultdict(lambda: defaultdict(list))
    for event in events:
        for schedule_item in event.schedule:
            event_dt = schedule_item.datetime
            date_key = event_dt.strftime("%Y-%m-%d")
            time_key = event_dt.strftime("%H:%M")
            events_by_date[date_key][time_key].append(event)

    # Sort dates and times
    sorted_events_by_date = sorted(events_by_date.items())

    final_structure = {}
    for date, times in sorted_events_by_date:
        sorted_times = sorted(times.items())
        final_structure[date] = dict(sorted_times)

    return final_structure


@app.get("/")
async def read_schedule(request: Request, session: Session = Depends(get_session)):
    """
    Fetches and renders the event schedule
    """

    now = datetime.now()
    events = month_events(session, now.month, now.year)
    event_data = generate_event_list_data(events)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "event_data": event_data,
            "now": now,
        },
    )


@app.get("/{date}")
async def read_date(
    request: Request, date: str, session: Session = Depends(get_session)
):
    if len(date) == 7:  # YYYY-MM
        year, month = int(date[:4]), int(date[5:])
        events = month_events(session, month, year)
    elif len(date) == 10:  # YYYY-MM-DD
        year, month, day = int(date[:4]), int(date[5:7]), int(date[8:])
        events = day_events(session, day, month, year)
    else:
        raise HTTPException(status_code=400, detail="Invalid date format")

    event_data = generate_event_list_data(events)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "event_data": event_data,
            "now": datetime(year, month, 1),
        },
    )
