from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class EventData(BaseModel):
    title: str
    description: str
    schedule: list[datetime]
    duration: timedelta | None = None
    author: str | None = Field(
        description=(
            "Author of the event, if available. "
            "If the event is a movie, this should be the director."
        )
    )
