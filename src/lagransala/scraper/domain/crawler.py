from datetime import datetime, timedelta
from typing import Protocol

from pydantic import BaseModel, HttpUrl


class CrawlResult(BaseModel):
    start_url: HttpUrl
    date: datetime
    duration: timedelta
    pages: set[str] = set()


class Crawler(Protocol):
    async def run(self, start_url: HttpUrl) -> CrawlResult: ...
