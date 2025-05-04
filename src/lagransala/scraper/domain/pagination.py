from enum import Enum
from typing import Self

from pydantic import BaseModel, model_validator


class PaginationType(Enum):
    NONE = "none"
    SIMPLE = "simple"
    DAY = "day"
    MONTH = "month"


class Pagination(BaseModel):
    type: PaginationType | None = None
    url: str
    limit: int | None = None
    simple_start_from: int | None = None
    date_format: str | None = None

    @model_validator(mode="after")
    def validate_pagination(self) -> Self:
        match self.type:
            case PaginationType.NONE | None:
                assert (
                    self.limit is None
                ), "Pagination limit must be None for PaginationType.NONE"
                assert (
                    self.simple_start_from is None
                ), "Pagination start from must be None for PaginationType.NONE"
                assert (
                    self.date_format is None
                ), "Date format must be None for PaginationType.NONE"
            case PaginationType.SIMPLE:
                assert "{n}" in self.url, "Simple pagination URL must contain '{n}'"
                assert (
                    self.simple_start_from is not None
                ), "Simple pagination start from must be set"
                assert self.limit is not None, "Simple pagination limit must be set"
            case PaginationType.DAY:
                assert "{date}" in self.url, "Day pagination URL must contain '{date}'"
                assert (
                    self.date_format is not None
                ), "Date format must be set for Day pagination"
                assert self.limit is not None, "Day pagination limit must be set"
            case PaginationType.MONTH:
                assert (
                    "{month}" in self.url
                ), "Month pagination URL must contain '{month}'"
                assert (
                    self.date_format is not None
                ), "Date format must be set for Month pagination"
                assert self.limit is not None, "Month pagination limit must be set"
        return self
