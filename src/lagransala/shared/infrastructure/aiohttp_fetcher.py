import asyncio
from datetime import datetime
from typing import Generator, Iterable

import aiohttp
from loguru import logger
from pydantic import HttpUrl

from ..application import cached
from ..domain import CacheBackend
from ..domain.fetcher import Response


class AiohttpFetcher:
    def __init__(
        self,
        client: aiohttp.ClientSession,
        max_concurrency: int = 12,
        cache_backend: CacheBackend[Response] | None = None,
        cache_ttl: int | None = None,
    ):
        self._client = client
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._cache_backend = cache_backend
        self._cache_ttl = cache_ttl

    async def fetch(self, url: HttpUrl) -> Response:
        if self._cache_backend:
            return await cached(
                backend=self._cache_backend,
                ttl=self._cache_ttl,
                key_params=["url"],
            )(self._fetch)(url=url)
        return await self._fetch(url)

    async def _fetch(self, url: HttpUrl) -> Response:
        logger.debug(f"fetching {url}")
        async with self._semaphore:
            async with self._client.get(str(url)) as response:
                return Response(
                    url=url,
                    status=response.status,
                    content=await response.text(),
                    content_type=response.content_type,
                    dt=datetime.now(),
                )

    async def fetch_urls(self, urls: Iterable[HttpUrl]) -> list[Response]:
        return await asyncio.gather(*[self.fetch(url) for url in urls])

    def fetch_task(self, url: HttpUrl) -> asyncio.Task[Response]:
        return asyncio.create_task(self.fetch(url))

    def fetch_urls_tasks(
        self, urls: Iterable[HttpUrl]
    ) -> Generator[asyncio.Task[Response]]:
        return (self.fetch_task(url) for url in urls)
