from pydantic import HttpUrl

from lagransala.shared.domain.fetcher import Fetcher

from ..domain import ContentFormat, SourcedContent


async def fetch_sourced_content(fetcher: Fetcher, url: HttpUrl) -> SourcedContent:
    response = await fetcher.fetch(url)
    return SourcedContent(
        url=url, content=response.content, fmt=ContentFormat.HTML, dt=response.dt
    )
