import asyncio
import logging
import re
from datetime import datetime
from typing import Callable
from urllib.parse import urljoin, urlparse

import aiohttp
from pydantic import HttpUrl, ValidationError

from lagransala.scraper.domain.crawler import CrawlResult
from lagransala.shared.application.urls import extract_urls

logger = logging.getLogger(__name__)


def _format_url(url: str | HttpUrl) -> str:
    if isinstance(url, HttpUrl):
        url = str(url)
    parsed_url = urlparse(url)
    return (
        f"{parsed_url.path}?{parsed_url.query}" if parsed_url.query else parsed_url.path
    )


class AiohttpCrawler:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        max_concurrency: int = 5,
        url_filter: Callable[[HttpUrl], bool] = lambda _: True,
    ) -> None:
        self.session = session
        self.url_filter = url_filter
        self._start_url_host: str
        self._visited: set[HttpUrl] = set()
        self._queue: asyncio.Queue[HttpUrl] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _fetch_and_extract(self, url: HttpUrl) -> None:
        async with self._semaphore:
            async with self.session.get(str(url)) as response:
                if response.status != 200:
                    return
                if response.content_type != "text/html":
                    return
                try:
                    text = await response.text()
                except UnicodeDecodeError:
                    return

        async with self._lock:
            self._visited.add(url)

        for url_str in extract_urls(text):
            if not re.match(r"^https?://", url_str):
                url_str = urljoin(str(url), url_str)

            try:
                next_url = HttpUrl(url_str)
            except ValidationError:
                continue

            host = urlparse(url_str).netloc
            async with self._lock:
                if next_url not in self._visited and host == self._start_url_host:
                    self._visited.add(next_url)
                    await self._queue.put(next_url)

    async def run(self, start_url: HttpUrl) -> CrawlResult:
        date = datetime.now()
        self._queue.put_nowait(start_url)
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

        self._visited.discard(start_url)

        return CrawlResult(
            start_url=start_url,
            date=date,
            duration=datetime.now() - date,
            pages={_format_url(url) for url in self._visited if self.url_filter(url)},
        )
