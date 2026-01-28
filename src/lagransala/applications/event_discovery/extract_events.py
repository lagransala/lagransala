import asyncio
from datetime import datetime
from typing import Generator, Iterable

from loguru import logger

from lagransala.extractor.domain import (
    ContentFormat,
    EmptyReason,
    EventExtractor,
    SourcedContent,
    SourcedEventExtraction,
)


def extract_event(
    extractor: EventExtractor,
    sourced_content: SourcedContent,
) -> asyncio.Task[SourcedEventExtraction]:

    async def task(content: SourcedContent):
        if content.fmt != ContentFormat.EMPTY:
            try:
                event = await extractor.extract(content)
            except Exception as e:
                logger.error(
                    f"Error extracting events from {content.url}", exc_info=True
                )
                raise e from e
            logger.info(f"Extracted {len(event.events)} events from {content.url}")
            return event
        else:
            logger.warning(f"No content found at {content.url}")
            return SourcedEventExtraction(
                model=None,
                source_url=content.url,
                events=[],
                empty_reason=EmptyReason.EMPTY_CONTENT,
                dt=datetime.now(),
            )

    return asyncio.create_task(task(sourced_content))


def extract_events(
    event_extractor: EventExtractor,
    sourced_contents: Iterable[SourcedContent],
) -> Generator[asyncio.Task[SourcedEventExtraction]]:

    return (extract_event(event_extractor, content) for content in sourced_contents)
