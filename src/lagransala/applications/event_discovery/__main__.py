import asyncio
import logging
from dataclasses import dataclass

import aiohttp
import instructor
from aiolimiter import AsyncLimiter
from litellm import acompletion
from sqlmodel import Session, select

from lagransala.extractor.domain import EventExtractionResult
from lagransala.extractor.infrastructure import InstructorEventExtractor
from lagransala.schedule.application import (
    seed_venues,
)
from lagransala.schedule.domain import Venue
from lagransala.scraper.application import pagination_elements
from lagransala.scraper.domain.content_scraper_repo import ContentScraperRepo
from lagransala.scraper.infrastructure import JsonContentScraperRepo, JsonPaginationRepo
from lagransala.shared.application import extract_markdown
from lagransala.shared.domain import coroutine_with_data
from lagransala.shared.domain.fetcher import Response
from lagransala.shared.infrastructure import FileCacheBackend
from lagransala.shared.infrastructure.aiohttp_fetcher import AiohttpFetcher
from lagransala.shared.infrastructure.initialize_sqlmodel import initialize_sqlmodel

from .get_venue_content_scraper import get_venue_content_scraper
from .get_venue_pagination import get_venue_pagination

logger = logging.getLogger(__name__)


@dataclass
class State:
    url: str
    venue: Venue
    content: str | None = None
    extraction_result: EventExtractionResult | None = None

    def with_content(self, content: str):
        return State(
            url=self.url,
            venue=self.venue,
            content=content,
            extraction_result=self.extraction_result,
        )

    def with_extraction_result(self, result: EventExtractionResult):
        return State(
            url=self.url,
            venue=self.venue,
            content=self.content,
            extraction_result=result,
        )

    def md_content(self, repo: ContentScraperRepo) -> str | None:
        if self.content is None:
            return None
        main_selector = get_venue_content_scraper(repo, self.venue).main_selector
        if main_selector is None:
            return None
        return extract_markdown(self.content, main_selector)


async def main():

    db_engine = initialize_sqlmodel("sqlite:///./lagransala.db")

    with Session(db_engine) as session:
        seed_venues(session, "./seeds/venues.json")
        venues = session.exec(select(Venue).order_by(Venue.name)).all()
        logger.info("Found %d venues", len(venues))

    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
    ) as client:
        fetcher = AiohttpFetcher(
            client,
            cache_backend=FileCacheBackend(Response, cache_dir=".cache/extract"),
            cache_ttl=3600 * 24,  # 1 day
        )

        pagination_repo = JsonPaginationRepo("./seeds/paginations.json")

        state: list[State] = []

        logger.info("1. Fetching page list")

        for venue in venues:
            pagination = get_venue_pagination(pagination_repo, venue)
            urls = await pagination_elements(fetcher, pagination)
            logger.info("Found %d pages for venue '%s'", len(urls), venue.name)
            for url in urls:
                state.append(State(url=url, venue=venue))

        logger.info("2. Fetching pages")

        tasks = [
            asyncio.create_task(
                coroutine_with_data(
                    fetcher.fetch(el.url),
                    el,
                    lambda content, el: el.with_content(content.content),
                )
            )
            for el in state
        ]
        state = await asyncio.gather(*tasks)

    logger.info("3. Extracting events")

    instructor_client = instructor.from_litellm(acompletion, mode=instructor.Mode.JSON)

    event_extractor = InstructorEventExtractor(
        instructor_client,
        "gemini/gemini-2.5-flash",
        AsyncLimiter(15),
        cache_backend=FileCacheBackend(
            EventExtractionResult, cache_dir=".cache/extract"
        ),
    )

    content_scraper_repo = JsonContentScraperRepo("./seeds/content_scrapers.json")

    tasks = [
        asyncio.create_task(
            coroutine_with_data(
                event_extractor.extract(el.md_content(content_scraper_repo) or ""),
                el,
                lambda result, el: el.with_extraction_result(result),
            )
        )
        for el in state
        if el.md_content is not None
    ]

    state = await asyncio.gather(*tasks)
