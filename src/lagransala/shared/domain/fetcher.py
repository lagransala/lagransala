from typing import Protocol, overload

from pydantic import BaseModel


class Response(BaseModel):
    status: int
    content: str
    content_type: str


class Fetcher(Protocol):

    async def fetch(self, url: str) -> Response: ...

    async def fetch_urls(self, urls: list[str]) -> list[Response]: ...
