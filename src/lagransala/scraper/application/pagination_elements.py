from typing import Pattern

from loguru import logger
from pydantic import HttpUrl

from lagransala.shared.application import absolutize_url, extract_urls
from lagransala.shared.domain import Fetcher

from ..domain import Pagination


async def pagination_elements(fetcher: Fetcher, pagination: Pagination) -> set[HttpUrl]:
    result: set[HttpUrl] = set()
    logger.debug(f"Fetching paginated pages for venue_slug '{pagination.venue_slug}'")
    responses = await fetcher.fetch_urls(url for url in pagination.urls())

    for response in responses:
        extracted = extract_urls(response.content, pagination.element_url_pattern)
        for url in extracted:
            result.add(HttpUrl(absolutize_url(str(pagination.base_url), url)))
    return result
