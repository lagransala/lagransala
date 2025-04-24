import asyncio
import logging

import aiohttp
from pydantic import HttpUrl

from lagransala.scraper.infrastructure.aiohttp_crawler import AiohttpCrawler


async def test():
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
        start_url = HttpUrl("https://elvivero.es/")
        result = await crawler.run(start_url)
        print(
            f"Found {len(result.pages)} pages in {result.duration.total_seconds()} seconds."
        )
        for page in sorted(result.pages):
            print(f"https://{start_url.host}{page}")


def main():
    asyncio.run(test())


if __name__ == "__main__":
    main()
