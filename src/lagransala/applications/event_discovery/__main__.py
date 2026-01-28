import asyncio
from datetime import datetime

import aiohttp
import instructor
from aiolimiter import AsyncLimiter
from groq import AsyncGroq, Groq
from langfuse import get_client, observe
from loguru import logger
from sqlalchemy import Engine
from sqlmodel import Session, select

from lagransala.extractor.domain import EventExtractor, SourcedEventExtraction
from lagransala.extractor.infrastructure import (
    GroqEventExtractor,
    InstructorEventExtractor,
)
from lagransala.schedule.application import seed_venues
from lagransala.schedule.domain import Event, EventDateTime, Venue
from lagransala.scraper.application import pagination_elements
from lagransala.scraper.domain import ContentScraper, Pagination
from lagransala.scraper.infrastructure import JsonContentScraperRepo, JsonPaginationRepo
from lagransala.shared.application.urls import extract_dates
from lagransala.shared.domain import FetcherResponse
from lagransala.shared.infrastructure import (
    AiohttpFetcher,
    FileCacheBackend,
    initialize_sqlmodel,
)

from . import (
    extract_events,
    get_venue_content_scraper,
    get_venue_pagination,
    scrape_content,
)

langfuse = get_client()


async def load_venues(db_engine: Engine):
    with Session(db_engine) as session:
        seed_venues(session, "./seeds/venues.json")
        venues = session.exec(select(Venue).order_by(Venue.name)).all()
    return venues


@observe()
async def get_venue_events(
    venue: Venue,
    pagination: Pagination,
    scraper: ContentScraper,
    event_extractor: EventExtractor,
):
    langfuse.update_current_trace(tags=[venue.slug])
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
    ) as client:
        pagination_fetcher = AiohttpFetcher(
            client,
            cache_backend=FileCacheBackend(FetcherResponse, cache_dir=".cache/fetch"),
            cache_ttl=600,  # 10mins
        )

        logger.info("   - Fetching venue pages")
        pages = await pagination_elements(pagination_fetcher, pagination)

        content_fetcher = AiohttpFetcher(
            client,
            cache_backend=FileCacheBackend(FetcherResponse, cache_dir=".cache/fetch"),
            cache_ttl=3600 * 23,  # 23 hours
        )

        logger.info("   - Fetching page contents")
        responses = await asyncio.gather(*content_fetcher.fetch_urls_tasks(pages))

    logger.info("   - Scraping page contents")
    sourced_contents = scrape_content(scraper, responses)
    distant_future = datetime.now().replace(year=5000)
    sourced_contents = sorted(
        list(sourced_contents),
        key=lambda x: (
            min(extract_dates(x.content), default=distant_future)
            if x.content
            else distant_future
        ),
    )

    logger.info("   - Extracting event data")
    # for extraction_result in asyncio.as_completed(
    #     extract_events(event_extractor, sourced_contents)
    # ):
    #     try:
    #         extraction = await extraction_result
    #     except Exception:
    #         logger.error("Error during event extraction", exc_info=True)
    #     else:
    #         logger.info(
    #             "     - Extracted %d events from %s",
    #             len(extraction.events),
    #             extraction.source_url,
    #         )
    #         for event_data in extraction.events:
    #             yield Event(
    #                 venue_id=venue.id,
    #                 schedule=[EventDateTime(datetime=dt) for dt in event_data.schedule],
    #                 author=event_data.author,
    #                 url=extraction.source_url,
    #                 title=event_data.title,
    #                 description=event_data.description,
    #                 duration=event_data.duration,
    #             )

    extraction_results = await asyncio.gather(
        *extract_events(event_extractor, sourced_contents), return_exceptions=True
    )

    for error in filter(lambda e: isinstance(e, BaseException), extraction_results):
        logger.error(f"Error during event extraction: {error}")

    events: list[Event] = []

    for result in filter(
        lambda r: isinstance(r, SourcedEventExtraction), extraction_results
    ):
        assert isinstance(result, SourcedEventExtraction)
        logger.debug(
            f"     - extracted {len(result.events)} events from {result.source_url}",
        )
        for event_data in result.events:
            logger.debug(
                f"       - {event_data.title} ({[dt.strftime('%Y-%m-%d %H:%M:%S') for dt in event_data.schedule]})"
            )
            events.append(
                Event(
                    venue_id=venue.id,
                    schedule=[EventDateTime(datetime=dt) for dt in event_data.schedule],
                    author=event_data.author,
                    url=result.source_url,
                    title=event_data.title,
                    description=event_data.description,
                    duration=event_data.duration,
                )
            )
    return events


def initialize_instructor_extractor():
    from litellm import litellm

    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]
    litellm._turn_on_debug()  # type: ignore[attr-defined]

    instructor_client = instructor.from_litellm(
        litellm.acompletion, mode=instructor.Mode.JSON
    )

    return InstructorEventExtractor(
        instructor_client,
        "groq/meta-llama/llama-4-scout-17b-16e-instruct",
        AsyncLimiter(8),
        cache_backend=FileCacheBackend(
            SourcedEventExtraction, cache_dir=".cache/extract"
        ),
    )


def initialize_groq_extractor():
    return GroqEventExtractor(
        # "meta-llama/llama-4-scout-17b-16e-instruct",
        # "meta-llama/llama-4-scout-17b-16e-instruct",
        # "meta-llama/llama-guard-4-12b",
        "openai/gpt-oss-120b",
        # "qwen/qwen3-32b",
        limiter=AsyncLimiter(30),
        cache_backend=FileCacheBackend(
            SourcedEventExtraction, cache_dir=".cache/extract"
        ),
    )


async def main():
    # db_engine = initialize_sqlmodel("sqlite:///:memory:")
    db_engine = initialize_sqlmodel("sqlite:///lagransala.db")
    venues = sorted(list(await load_venues(db_engine)), key=lambda v: v.name)
    json_pagination_repo = JsonPaginationRepo("./seeds/paginations.json")
    content_scraper_repo = JsonContentScraperRepo("./seeds/content_scrapers.json")
    logger.info(f"Loaded {len(venues)} venues")

    # event_extractor = initialize_instructor_extractor()
    event_extractor = initialize_groq_extractor()

    with Session(db_engine) as session:
        old_events = session.exec(select(Event)).all()
        for event in old_events:
            for dt in event.schedule:
                session.delete(dt)
            session.delete(event)
        session.commit()

        for venue in venues:
            logger.info(f"- Processing venue: {venue.slug}")
            pagination = get_venue_pagination(json_pagination_repo, venue)
            scraper = get_venue_content_scraper(content_scraper_repo, venue)

            #     async for event in get_venue_events(
            #         venue, pagination, scraper, event_extractor
            #     ):
            #         logger.info("Saving event: %s", event.title)
            #         session.add(event)
            #         session.commit()

            events = await get_venue_events(venue, pagination, scraper, event_extractor)

            logger.info(f"- Adding {len(events)} events for venue: {venue.slug}")
            with Session(db_engine) as session:
                for event in events:
                    session.add(event)
                session.commit()
