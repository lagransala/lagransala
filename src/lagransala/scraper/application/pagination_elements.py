from typing import Pattern

from aiohttp import ClientSession

from lagransala.scraper.domain.pagination import Pagination
from lagransala.shared.application.urls import extract_urls


async def pagination_elements(
    session: ClientSession, pagination: Pagination, url_pattern: str | Pattern[str]
) -> set[str]:
    urls: set[str] = set()
    for url in pagination.urls():
        async with session.get(str(url)) as response:
            urls.update(extract_urls(await response.text(), url_pattern))
    return urls
