from datetime import datetime
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field, HttpUrl

from lagransala.extractor.domain import EventData

from .sourced_content import SourcedContent


class EmptyReason(Enum):
    ONLY_PAST = "only_past"
    NO_EVENTS_FOUND = "no_events_found"
    EMPTY_CONTENT = "empty_content"
    EXTRACTION_ERROR = "extraction_error"


class EventExtraction(BaseModel):
    events: list[EventData]
    empty_reason: EmptyReason | None = Field(description="Reason for empty list")


class SourcedEventExtraction(EventExtraction):
    model: str | None
    source_url: HttpUrl
    dt: datetime


# TODO: include in EventExtractor (custom cache logic)
class FailedExtraction(Enum):
    RATE_LIMIT = "rate_limit"
    VALIDATION_ERROR = "validation_error"


class EventExtractor(Protocol):
    async def extract(
        self, content: SourcedContent, context: dict[str, str] | None = None
    ) -> SourcedEventExtraction: ...
