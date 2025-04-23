from datetime import datetime, timedelta

from pydantic import BaseModel, HttpUrl


class CrawlResult(BaseModel):
    start_url: HttpUrl
    date: datetime
    duration: timedelta
    pages: set[str] = set()
