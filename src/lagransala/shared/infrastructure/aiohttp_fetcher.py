import asyncio
import logging

import aiohttp

from ..application import cached
from ..domain import CacheBackend
from ..domain.fetcher import Response

logger = logging.getLogger(__name__)


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

        if self._cache_backend is not None:
            self.fetch = cached(
                backend=self._cache_backend,
                ttl=cache_ttl,
                key_params=["url"],
            )(self._fetch)
        else:
            self.fetch = self._fetch

    async def _fetch(self, url: str) -> Response:
        """
        Fetches data from the given URL asynchronously.
        :param url: The URL to fetch data from.
        :return: The response text from the URL.
        """
        async with self._client.get(url) as response:
            return Response(
                status=response.status,
                content=await response.text(),
                content_type=response.content_type,
            )

    async def fetch_urls(self, urls: list[str]) -> list[Response]:
        """
        Fetches data from multiple URLs concurrently.
        :param urls: List of URLs to fetch data from.
        :return: List of responses from the URLs.
        """
        async with self._semaphore:
            return await asyncio.gather(*[self.fetch(url) for url in urls])
