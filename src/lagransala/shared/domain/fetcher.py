import asyncio
from datetime import datetime
from typing import Iterable, Protocol

from pydantic import BaseModel, HttpUrl


class Response(BaseModel):
    url: HttpUrl
    status: int
    content: str
    content_type: str
    dt: datetime


class Fetcher(Protocol):

    async def fetch(self, url: HttpUrl) -> Response: ...

    async def fetch_urls(self, urls: Iterable[HttpUrl]) -> Iterable[Response]: ...

    def fetch_task(self, url: HttpUrl) -> asyncio.Task[Response]: ...

    def fetch_urls_tasks(
        self, urls: Iterable[HttpUrl]
    ) -> Iterable[asyncio.Task[Response]]: ...
