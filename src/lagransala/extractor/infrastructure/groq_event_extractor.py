import logging
from datetime import datetime
from textwrap import dedent
from typing import Any, Callable

from aiolimiter import AsyncLimiter
from groq import AsyncGroq, Groq
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
from lagransala.shared.infrastructure import groq_chat_completion

logger = logging.getLogger(__name__)


def key_func(
    _f: Callable, content: SourcedContent, context: dict[str, str] | None = None
) -> str:
    return content.cache_key


class GroqEventExtractor:
    def __init__(
        self,
        model: str,
        client: AsyncGroq | None = None,
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
        """)

        self._client = client or AsyncGroq()
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
                empty_reason=EmptyReason.EMPTY_CONTENT,
                dt=datetime.now(),
            )
        assert content.content is not None
        async with self._limiter:
            logger.debug("  - extracting events from %s", content.url)
            response = await groq_chat_completion(
                self._client,
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt.format(
                            first_day=datetime.strftime(
                                datetime.now().replace(day=1), "%Y-%m-%d"
                            ),
                        ),
                    },
                    {"role": "user", "content": content.content},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "event",
                        "schema": EventExtraction.model_json_schema(),
                    },
                },
            )
        json_response = response.choices[0].message.content
        if json_response is None:
            logger.error("No JSON response from %s", content.url)
            return SourcedEventExtraction(
                model=self._model,
                source_url=content.url,
                events=[],
                empty_reason=EmptyReason.EXTRACTION_ERROR,
                dt=datetime.now(),
            )
        try:
            event_extraction = EventExtraction.model_validate_json(json_response)
            return SourcedEventExtraction(
                model=self._model,
                source_url=content.url,
                events=event_extraction.events,
                empty_reason=event_extraction.empty_reason,
                dt=datetime.now(),
            )
        except ValidationError as e:
            logger.error("ValidationError parsing events from %s", content.url)
            for error in e.errors():
                logger.error(
                    "  > at %s: %s",
                    ".".join(map(str, error["loc"])),
                    error["msg"],
                )
            return SourcedEventExtraction(
                model=self._model,
                source_url=content.url,
                events=[],
                empty_reason=EmptyReason.EXTRACTION_ERROR,
                dt=datetime.now(),
            )
