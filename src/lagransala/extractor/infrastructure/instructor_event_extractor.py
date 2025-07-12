from datetime import datetime

import instructor
from aiolimiter import AsyncLimiter
from tenacity import AsyncRetrying, stop_after_attempt

from lagransala.extractor.domain import EventExtractionResult
from lagransala.shared.application.caching import cached
from lagransala.shared.domain.caching import CacheBackend


class InstructorEventExtractor:
    def __init__(
        self,
        client: instructor.AsyncInstructor,
        model: str,
        limiter: AsyncLimiter | None = None,
        cache_backend: CacheBackend[EventExtractionResult] | None = None,
        cache_ttl: int | None = None,
    ):
        self.system_prompt = """
            You are an event extractor.
            You will receive web page content in markdown format and you
            will extract all the events present in it.

            If you find no events, you will return an empty list. If you
            find only one event, you will return a list with one element.
            If you find multiple events, you will return a list with all the
            events. Be careful not to include the same event multiple times.

            If the same event occurs multiple times (has more than one date
            and/or time), you will return multiple events with the same
            title and description, but different time.

            Only include events that are happening today or in the future.
            The current date is {{ today }}.
        """

        self._client = client
        self._model = model
        self._limiter = limiter or AsyncLimiter(10, 60)
        self._cache_backend = cache_backend
        self._cache_ttl = cache_ttl

        if self._cache_backend is not None:
            self.extract = cached(
                backend=self._cache_backend,
                ttl=cache_ttl,
            )(self._extract)
        else:
            self.extract = self._extract

    async def _extract(
        self, content: str, _context: dict[str, str] | None = None
    ) -> EventExtractionResult:
        async with self._limiter:
            result = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=2**14,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": content,
                    },
                    # TODO: use context
                ],
                response_model=EventExtractionResult,
                context={
                    "today": datetime.strftime(datetime.now(), "%Y-%m-%d"),
                },
                max_retries=AsyncRetrying(stop=stop_after_attempt(0), reraise=True),
            )
            return result
