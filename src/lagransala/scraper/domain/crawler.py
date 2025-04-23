from typing import Protocol

from pydantic import HttpUrl

from lagransala.scraper.domain.crawl_result import CrawlResult


class Crawler(Protocol):
    async def run(self, start_url: HttpUrl) -> CrawlResult: ...
