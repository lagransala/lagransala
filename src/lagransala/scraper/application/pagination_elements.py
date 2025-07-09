from typing import Pattern

from aiohttp import ClientSession

from lagransala.scraper.domain import Pagination
from lagransala.shared.application import absolutize_url, extract_urls


async def pagination_elements(
    session: ClientSession, pagination: Pagination, url_pattern: str | Pattern[str]
) -> set[str]:
    urls: set[str] = set()
    for url in pagination.urls():
        async with session.get(str(url)) as response:
            extracted = extract_urls(await response.text(), url_pattern)
            for url in extracted:
                urls.add(absolutize_url(str(pagination.base_url), url))
    return urls
