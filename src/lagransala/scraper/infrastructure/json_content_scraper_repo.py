import logging
from pathlib import Path
from typing import overload

from pydantic import TypeAdapter, ValidationError

from ..domain import ContentScraper

logger = logging.getLogger(__name__)


class JsonContentScraperRepo:

    _adapter = TypeAdapter(list[ContentScraper])

    def __init__(self, file: Path | str):
        self._file = file if isinstance(file, Path) else Path(file)

        if not self._file.exists():
            self._file.write_text("[]")

    def add(self, content_scraper: ContentScraper) -> None:
        """Add a content_scraper to the repository."""
        content_scrapers = self.get()
        if content_scraper.venue_slug in {p.venue_slug for p in content_scrapers}:
            content_scrapers = [
                p if p.venue_slug != content_scraper.venue_slug else content_scraper
                for p in content_scrapers
            ]
        else:
            content_scrapers.append(content_scraper)
        data = self._adapter.dump_json(content_scrapers, indent=2)
        with open(self._file, "wb") as file:
            file.write(data)

    @overload
    def get(self, venue_slug: str) -> ContentScraper | None: ...

    @overload
    def get(self, venue_slug: None = None) -> list[ContentScraper]: ...

    def get(
        self, venue_slug: str | None = None
    ) -> list[ContentScraper] | ContentScraper | None:
        """Get a content_scraper by its ID or all content_scrapers if ID is None."""
        with open(self._file) as file:
            try:
                content_scrapers = self._adapter.validate_json(file.read())
            except ValidationError as e:
                for error in e.errors():
                    logger.error(
                        "Error in %s: %s: %s", self._file, error["loc"], error["msg"]
                    )
                raise ValueError(f"Error validating json {self._file}: {e}") from e
        if venue_slug:
            return next(
                filter(lambda p: p.venue_slug == venue_slug, content_scrapers), None
            )
        else:
            return content_scrapers
