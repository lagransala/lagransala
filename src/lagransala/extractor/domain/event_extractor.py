from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field

from lagransala.extractor.domain import EventData


class EmptyReason(Enum):
    ONLY_PAST = "only_past"
    NO_EVENTS_FOUND = "no_events_found"


class EventExtractionResult(BaseModel):
    events: list[EventData]
    empty_reason: EmptyReason | None = Field(description="Reason for empty list")


class EventExtractor(Protocol):
    async def extract(
        self, content: str, context: dict[str, str] | None = None
    ) -> EventExtractionResult: ...
