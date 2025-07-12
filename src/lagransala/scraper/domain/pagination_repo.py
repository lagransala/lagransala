from typing import Protocol, overload

from .pagination import Pagination


class PaginationRepo(Protocol):
    def add(self, pagination: Pagination) -> None:
        """Add a pagination to the repository."""
        ...

    @overload
    def get(self, venue_slug: str) -> Pagination | None: ...

    @overload
    def get(self, venue_slug: None = None) -> list[Pagination]: ...

    def get(
        self, venue_slug: str | None = None
    ) -> list[Pagination] | Pagination | None:
        """Get a pagination by its venue_slug or all paginations if venue_slug is None."""
        ...
