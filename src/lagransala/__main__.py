import asyncio
import logging
from pathlib import Path
from uuid import uuid4

import aiohttp
from pydantic import HttpUrl

from lagransala.scraper.application.pagination_elements import pagination_elements
from lagransala.scraper.domain.pagination import Pagination, PaginationType
from lagransala.scraper.infrastructure.aiohttp_crawler import AiohttpCrawler
from lagransala.scraper.infrastructure.json_pagination_repo import JsonPaginationRepo
from lagransala.shared.application.urls import extract_urls


async def test_crawler():
    """Console script for lagransala."""
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        },
    ) as session:
        crawler = AiohttpCrawler(session=session)
        start_url = HttpUrl("https://entradasfilmoteca.gob.es/")
        result = await crawler.run(start_url)
        print(
            f"Found {len(result.pages)} pages in {result.duration.total_seconds()} seconds."
        )
        for page in sorted(result.pages):
            print(f"https://{start_url.host}{page}")


async def test_pagination():
    pagination_repo = JsonPaginationRepo(Path("./assets/paginations.json"))
    paginations = pagination_repo.get()
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        },
    ) as session:
        for pagination in paginations:
            event_url_pattern = (
                "^(FichaPelicula\\.aspx\\?id=\\d+&idPelicula=\\d+|/actividades/[\\w-]+)"
            )
            urls = await pagination_elements(session, pagination, event_url_pattern)
            for url in sorted(urls):
                print(f"{url}")


def main():
    # asyncio.run(test_crawler())
    asyncio.run(test_pagination())


if __name__ == "__main__":
    main()
