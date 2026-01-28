import logging
from datetime import datetime
from textwrap import dedent

from aiolimiter import AsyncLimiter
from langfuse import observe

from lagransala.extractor.domain.event_extractor import (
    EmptyReason,
    EventExtraction,
    SourcedEventExtraction,
)
from lagransala.extractor.domain.sourced_content import ContentFormat, SourcedContent
from lagransala.shared.application.caching import cached
from lagransala.shared.domain import CacheBackend

logger = logging.getLogger(__name__)


class LitellmEventExtractor:
    def __init__(
        self,
        model: str,
        limiter: AsyncLimiter | None = None,
        cache_backend: CacheBackend[SourcedEventExtraction] | None = None,
        cache_ttl: int | None = None,
    ):
        from litellm import litellm

        litellm.enable_json_schema_validation = True
        self._litellm = litellm
        self.system_prompt = dedent(
            """
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
        """
        )

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
            )(
                self._extract
            )(content, context)
        else:
            return await self._extract(content, context)

    async def _extract(
        self, content: SourcedContent, context: dict[str, str] | None = None
    ) -> SourcedEventExtraction:
        if content.fmt == ContentFormat.EMPTY:
            return SourcedEventExtraction(
                source_url=content.url,
                events=[],
                empty_reason=EmptyReason.EMPTY_CONTENT,
                model=self._model,
                dt=datetime.now(),
            )
        assert content.content is not None
        async with self._limiter:
            logger.debug(
                "Extracting events from content with length %d", len(content.content)
            )
            response = self._litellm.completion(
                model=self._model,
                response_format=EventExtraction,
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
            )
            return SourcedEventExtraction(
                source_url=content.url,
                events=response.events,
                empty_reason=response.empty_reason,
                model=self._model,
                dt=datetime.now(),
            )
