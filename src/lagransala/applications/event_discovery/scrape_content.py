from typing import Iterable

from lagransala.extractor.application import sourced_content_to_md
from lagransala.extractor.domain import (
    ContentFormat,
    SourcedContent,
)
from lagransala.scraper.domain import ContentScraper
from lagransala.shared.domain import FetcherResponse


def scrape_content(
    scraper: ContentScraper, responses: Iterable[FetcherResponse]
) -> Iterable[SourcedContent]:
    return map(
        lambda response: sourced_content_to_md(
            SourcedContent(
                url=response.url, content=response.content, fmt=ContentFormat.HTML
            ),
            scraper.main_selector,
        ),
        responses,
    )
