import logging
from pathlib import Path
from typing import overload

from pydantic import TypeAdapter, ValidationError

from lagransala.scraper.domain.pagination import Pagination

logger = logging.getLogger(__name__)


class JsonPaginationRepo:

    _adapter = TypeAdapter(list[Pagination])

    def __init__(self, file: Path | str):
        self._file = file if isinstance(file, Path) else Path(file)

        if not self._file.exists():
            self._file.write_text("[]")

    def add(self, pagination: Pagination) -> None:
        """Add a pagination to the repository."""
        paginations = self.get()
        if pagination.venue_slug in {p.venue_slug for p in paginations}:
            paginations = [
                p if p.venue_slug != pagination.venue_slug else pagination
                for p in paginations
            ]
        else:
            paginations.append(pagination)
        data = self._adapter.dump_json(paginations, indent=2)
        with open(self._file, "wb") as file:
            file.write(data)

    @overload
    def get(self, venue_slug: str) -> Pagination | None: ...

    @overload
    def get(self, venue_slug: None = None) -> list[Pagination]: ...

    def get(
        self, venue_slug: str | None = None
    ) -> list[Pagination] | Pagination | None:
        """Get a pagination by its ID or all paginations if ID is None."""
        with open(self._file) as file:
            try:
                paginations = self._adapter.validate_json(file.read())
            except ValidationError as e:
                for error in e.errors():
                    logger.error(
                        "Error in %s: %s: %s", self._file, error["loc"], error["msg"]
                    )
                raise ValueError(f"Error validating json {self._file}: {e}") from e
        if venue_slug:
            return next(filter(lambda p: p.venue_slug == venue_slug, paginations), None)
        else:
            return paginations
