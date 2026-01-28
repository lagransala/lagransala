import hashlib
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, model_validator

logger = __import__("loguru").logger


class ContentFormat(Enum):
    MD = "markdown"
    HTML = "html"
    EMPTY = "empty"


class SourcedContent(BaseModel):
    url: HttpUrl
    content: str | None
    fmt: ContentFormat
    dt: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def check_content_format(self):
        if self.fmt == ContentFormat.EMPTY and self.content is not None:
            raise ValueError("Content must be None if format is EMPTY")
        return self

    @model_validator(mode="before")
    @classmethod
    def strip_content(cls, data: dict[Any, Any]):
        if isinstance(data["content"], str):
            data["content"] = data["content"].strip()
        if data["content"] == "" and data["fmt"] != ContentFormat.EMPTY:
            logger.debug(
                f"Content is empty, setting format to EMPTY for URL: {data['url']}"
            )
            data["fmt"] = ContentFormat.EMPTY
            data["content"] = None
        return data

    @property
    def cache_key(self) -> str:
        payload = (self.content or "").encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
