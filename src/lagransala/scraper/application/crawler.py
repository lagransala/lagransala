import asyncio
import logging
import re
from datetime import datetime
from typing import Callable
from urllib.parse import urljoin, urlparse

from pydantic import HttpUrl, ValidationError

from lagransala.scraper.domain.crawler import CrawlResult
from lagransala.shared.application.urls import extract_urls
from lagransala.shared.domain.fetcher import Fetcher

logger = logging.getLogger(__name__)


def _format_url(url: str | HttpUrl) -> str:
    if isinstance(url, HttpUrl):
        url = str(url)
    parsed_url = urlparse(url)
    return (
        f"{parsed_url.path}?{parsed_url.query}" if parsed_url.query else parsed_url.path
    )


class Crawler:
    def __init__(
        self,
        fetcher: Fetcher,
        max_concurrency: int = 5,
        url_filter: Callable[[HttpUrl], bool] = lambda _: True,
    ) -> None:
        self.fetcher = fetcher
        self.url_filter = url_filter
        self._start_url_host: str
        self._visited: set[HttpUrl] = set()
        self._processed_urls: set[HttpUrl] = set()
        self._queue: asyncio.Queue[HttpUrl] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _fetch_and_extract(self, url: HttpUrl) -> None:
        async with self._semaphore:
            response = await self.fetcher.fetch(str(url))

        if response.status != 200:
            return

        if "text/html" not in response.content_type:
            return

        text = response.content

        async with self._lock:
            self._processed_urls.add(url)

        for url_str in extract_urls(text):
            if not re.match(r"^https?://", url_str):
                url_str = urljoin(str(url), url_str)

            try:
                next_url = HttpUrl(url_str)
            except ValidationError:
                continue

            host = urlparse(str(next_url)).netloc
            async with self._lock:
                if next_url not in self._visited and host == self._start_url_host:
                    self._visited.add(next_url)
                    await self._queue.put(next_url)

    async def run(self, start_url: HttpUrl) -> CrawlResult:
        start = datetime.now()
        self._queue.put_nowait(start_url)
        self._visited.add(start_url)
        self._start_url_host = urlparse(str(start_url)).netloc

        while not self._queue.empty():
            current_batch = []
            while not self._queue.empty():
                current_batch.append(await self._queue.get())

            tasks = [
                asyncio.create_task(self._fetch_and_extract(url))
                for url in current_batch
            ]
            await asyncio.gather(*tasks)

        return CrawlResult(
            start_url=start_url,
            date=start,
            duration=datetime.now() - start,
            pages={
                _format_url(url)
                for url in self._processed_urls
                if self.url_filter(url) and url != start_url
            },
        )
