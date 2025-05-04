from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import HttpUrl, ValidationError
from sqlmodel import Session, SQLModel, create_engine, select

from lagransala.schedule.domain.event import Event, EventDateTime
from lagransala.schedule.domain.venue import Venue


@pytest.fixture(name="engine")
def engine_fixture(tmp_path):
    """Create an in-memory SQLite engine for testing."""
    db_file = tmp_path / "test.db"
    sqlite_url = f"sqlite:///{db_file}"
    engine = create_engine(sqlite_url, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Provide a new session for each test."""
    with Session(engine) as session:
        yield session


def test_event_get_urls_empty(session):
    """get_urls returns empty set when no events."""
    urls = Event.get_urls(session)
    assert isinstance(urls, set)
    assert urls == set()


def test_event_get_urls_non_empty(session):
    """get_urls returns unique set of event URLs."""
    # Create two events with distinct URLs
    ev1 = Event(
        url=HttpUrl("https://example.com/1"),
        title="Event 1",
        author="Author A",
        description="Desc",
        duration=timedelta(hours=1),
        venue_id=uuid4(),
    )
    ev2 = Event(
        url=HttpUrl("https://example.com/2"),
        title="Event 2",
        author=None,
        description="Desc2",
        duration=None,
        venue_id=uuid4(),
    )
    session.add(ev1)
    session.add(ev2)
    session.commit()

    urls = Event.get_urls(session)
    expected = {HttpUrl("https://example.com/1"), HttpUrl("https://example.com/2")}
    assert urls == expected


def test_event_datetime_relationship(session):
    """Test that EventDateTime relates to Event and stores datetime correctly."""
    event = Event(
        url=HttpUrl("https://example.com/schedule"),
        title="SchedEvent",
        author="SchedAuthor",
        description="Scheduled",
        duration=timedelta(minutes=30),
        venue_id=uuid4(),
    )
    session.add(event)
    session.commit()
    # Add datetime entries
    dt1 = EventDateTime(event_id=event.id, datetime=datetime(2025, 5, 4, 10, 0))
    dt2 = EventDateTime(event_id=event.id, datetime=datetime(2025, 5, 5, 12, 0))
    session.add(dt1)
    session.add(dt2)
    session.commit()

    # Refresh event to load relationship
    session.refresh(event)
    datetimes = sorted([ed.datetime for ed in event.schedule])
    assert datetimes == [datetime(2025, 5, 4, 10, 0), datetime(2025, 5, 5, 12, 0)]
