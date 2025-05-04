from datetime import datetime, timedelta
from enum import Enum
from typing import Self

from pydantic import UUID4, BaseModel, HttpUrl, model_validator


class PaginationType(Enum):
    NONE = "none"
    SIMPLE = "simple"
    DAY = "day"
    MONTH = "month"


type PaginationID = UUID4


class Pagination(BaseModel):
    id: PaginationID
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

    def urls(self) -> list[HttpUrl]:
        match self.type:
            case PaginationType.NONE | None:
                return [HttpUrl(self.url)]
            case PaginationType.SIMPLE:
                assert self.simple_start_from is not None
                assert self.limit is not None
                return [
                    HttpUrl(self.url.format(n=i))
                    for i in range(
                        self.simple_start_from,
                        self.limit + self.simple_start_from,
                    )
                ]
            case PaginationType.DAY:
                assert self.date_format is not None
                assert self.limit is not None
                today = datetime.now().replace(minute=0, hour=0, second=0)
                result: list[HttpUrl] = []
                for i in range(0, self.limit):
                    date = today + timedelta(days=i)
                    url = HttpUrl(self.url.format(date=date.strftime(self.date_format)))
                    result.append(url)
                return result
            case PaginationType.MONTH:
                assert self.date_format is not None
                assert self.limit is not None
                month_start = datetime.now().replace(day=1, minute=0, hour=0, second=0)
                current_month = month_start.month
                result: list[HttpUrl] = []
                for i in range(0, self.limit):
                    month = month_start.replace(month=current_month + i)
                    print(month)
                    url = HttpUrl(
                        self.url.format(month=month.strftime(self.date_format))
                    )

                    result.append(url)
                return result
