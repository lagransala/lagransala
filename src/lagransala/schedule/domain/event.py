from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import UUID4, HttpUrl
from sqlmodel import Field, Relationship, Session, SQLModel, select

from lagransala.shared.application.build_sqlmodel_type import build_sqlmodel_type

if TYPE_CHECKING:
    from .venue import Venue


class Event(SQLModel, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True)
    schedule: list["EventDateTime"] = Relationship(back_populates="event")
    venue_id: UUID = Field(default=None, foreign_key="venue.id")
    venue: "Venue" = Relationship(back_populates="events")

    url: HttpUrl = Field(sa_type=build_sqlmodel_type(HttpUrl))
    title: str
    author: str | None
    description: str
    duration: timedelta | None

    @classmethod
    def get_urls(cls, session: Session) -> set[HttpUrl]:
        return set(map(lambda event: event.url, session.exec(select(Event)).all()))


class EventDateTime(SQLModel, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True)

    event_id: UUID4 = Field(default=None, foreign_key="event.id")
    event: Event = Relationship(back_populates="schedule")

    datetime: datetime  # TODO: validate aware datetime
