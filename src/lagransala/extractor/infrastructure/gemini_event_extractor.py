from datetime import datetime
from textwrap import dedent
from typing import Any, Callable

from aiolimiter import AsyncLimiter
from google import genai
from langfuse import observe
from pydantic import ValidationError

from lagransala.extractor.domain.event_extractor import (
    EmptyReason,
    EventExtraction,
    SourcedEventExtraction,
)
from lagransala.extractor.domain.sourced_content import ContentFormat, SourcedContent
from lagransala.shared.application import cached
from lagransala.shared.domain import CacheBackend
from lagransala.shared.infrastructure.logging import logger


def key_func(
    _f: Callable, content: SourcedContent, context: dict[str, str] | None = None
) -> str:
    return content.cache_key


class GeminiEventExtractor:
    def __init__(
        self,
        model: str,
        client: genai.Client | None = None,
        limiter: AsyncLimiter | None = None,
        cache_backend: CacheBackend[SourcedEventExtraction] | None = None,
        cache_ttl: int | None = None,
    ):
        self.system_prompt = dedent("""
            You are an event extractor.
            You will receive web page content in markdown format and you
            will extract all the events present in it.

            If you find no events, you will return an empty list. If you
            find only one event, you will return a list with one element.
            If you find multiple events, you will return a list with all the
            events. Be careful not to include the same event multiple times.

            If the same event occurs multiple times (has more than one date
            and/or time), you will include it only once in the list, with
            the datetimes aggregated into the schedule list.

            Only include events that are happening from the start of this month .
            The first day of the month was {first_day}.

            Here is the markdown content from the web page:

            {content}
        """)

        self._client = client or genai.Client()
        self._model = model
        self._limiter = limiter or AsyncLimiter(10, 60)
        self._cache_backend = cache_backend
        self._cache_ttl = cache_ttl

    @observe()
    async def extract(
        self, content: SourcedContent, context: dict[str, str] | None = None
    ) -> SourcedEventExtraction:
        if self._cache_backend is not None:
            return await cached(
                backend=self._cache_backend,
                ttl=self._cache_ttl,
                key_func=key_func,
            )(self._extract)(content, context)
        else:
            return await self._extract(content, context)

    async def _extract(
        self, content: SourcedContent, context: dict[str, str] | None = None
    ) -> SourcedEventExtraction:
        if content.fmt == ContentFormat.EMPTY:
            return SourcedEventExtraction(
                model=self._model,
                source_url=content.url,
                events=[],
                dt=datetime.now(),
                empty_reason=EmptyReason.EMPTY_CONTENT,
            )
        assert content.content is not None
        async with self._limiter:
            logger.debug(f"  - extracting events from {content.url}")
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=self.system_prompt.format(
                    first_day=datetime.strftime(
                        datetime.now().replace(day=1), "%Y-%m-%d"
                    ),
                ),
                config={
                    "response_mime_type": "application/json",
                    "response_schema": EventExtraction.model_json_schema(),
                },
            )
        extraction: EventExtraction | None = None
        try:
            match response.parsed:
                case EventExtraction() as event_extraction:
                    extraction = event_extraction
                case dict() as json_response:
                    extraction = EventExtraction.model_validate(json_response)
                case None:
                    if response.text is not None:
                        extraction = EventExtraction.model_validate_json(response.text)
                case _:
                    extraction = None
        except ValidationError as e:
            logger.error(f"ValidationError parsing events from {content.url}")
            for error in e.errors():
                logger.error(
                    f"  > at {'.'.join(map(str, error['loc']))}: {error['msg']}"
                )
        finally:
            if extraction is None:
                return SourcedEventExtraction(
                    model=self._model,
                    source_url=content.url,
                    events=[],
                    empty_reason=EmptyReason.EXTRACTION_ERROR,
                    dt=datetime.now(),
                )
            else:
                return SourcedEventExtraction(
                    model=self._model,
                    source_url=content.url,
                    events=extraction.events,
                    empty_reason=extraction.empty_reason,
                    dt=datetime.now(),
                )
