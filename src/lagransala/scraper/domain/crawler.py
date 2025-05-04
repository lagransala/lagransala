from datetime import datetime, timedelta

from pydantic import BaseModel, HttpUrl
from typing import Protocol

from pydantic import HttpUrl

class CrawlResult(BaseModel):
    start_url: HttpUrl
    date: datetime
    duration: timedelta
    pages: set[str] = set()

class Crawler(Protocol):
    async def run(self, start_url: HttpUrl) -> CrawlResult: ...
