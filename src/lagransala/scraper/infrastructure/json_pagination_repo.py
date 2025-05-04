from pathlib import Path
from typing import overload

from pydantic import TypeAdapter

from lagransala.scraper.domain.pagination import Pagination, PaginationID


class JsonPaginationRepo:

    _adapter = TypeAdapter(list[Pagination])

    def __init__(self, file: Path):
        self._file = file

        if not self._file.exists():
            self._file.write_text("[]")

    def add(self, pagination: Pagination) -> None:
        """Add a pagination to the repository."""
        paginations = self.get()
        if pagination.id in {p.id for p in paginations}:
            paginations = [
                p if p.id != pagination.id else pagination for p in paginations
            ]
        else:
            paginations.append(pagination)
        data = self._adapter.dump_json(paginations, indent=2)
        with open(self._file, "wb") as file:
            file.write(data)

    @overload
    def get(self, id: PaginationID) -> Pagination | None: ...

    @overload
    def get(self, id: None = None) -> list[Pagination]: ...

    def get(
        self, id: PaginationID | None = None
    ) -> list[Pagination] | Pagination | None:
        """Get a pagination by its ID or all paginations if ID is None."""
        with open(self._file) as file:
            paginations = self._adapter.validate_json(file.read())
        if id:
            return next(filter(lambda p: p.id == id, paginations), None)
        else:
            return paginations
