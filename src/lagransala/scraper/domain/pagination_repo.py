from typing import Protocol, overload

from lagransala.scraper.domain.pagination import Pagination, PaginationID


class PaginationRepo(Protocol):
    def add(self, pagination: Pagination) -> None:
        """Add a pagination to the repository."""
        ...

    @overload
    def get(self, id: PaginationID) -> Pagination | None: ...

    @overload
    def get(self, id: None = None) -> list[Pagination]: ...

    def get(
        self, id: PaginationID | None = None
    ) -> list[Pagination] | Pagination | None:
        """Get a pagination by its ID or all paginations if ID is None."""
        ...
