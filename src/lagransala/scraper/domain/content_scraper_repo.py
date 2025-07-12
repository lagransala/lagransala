from typing import Protocol, overload

from .content_scraper import ContentScraper


class ContentScraperRepo(Protocol):
    def add(self, content_scraper: ContentScraper) -> None:
        """Add a pagination to the repository."""
        ...

    @overload
    def get(self, venue_slug: str) -> ContentScraper | None: ...

    @overload
    def get(self, venue_slug: None = None) -> list[ContentScraper]: ...

    def get(
        self, venue_slug: str | None = None
    ) -> list[ContentScraper] | ContentScraper | None:
        """Get a pagination by its venue_slug or all paginations if venue_slug is None."""
        ...
