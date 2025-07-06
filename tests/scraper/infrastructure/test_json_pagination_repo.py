import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import UUID4, HttpUrl

from lagransala.scraper.domain.pagination import Pagination, PaginationType
from lagransala.scraper.infrastructure.json_pagination_repo import JsonPaginationRepo


def create_sample_pagination(id: UUID4 | None = None):
    """Helper to create a valid simple pagination"""
    if id is None:
        id = uuid4()
    return Pagination(
        id=id,
        type=PaginationType.SIMPLE,
        url="https://example.com/page/{n}",
        limit=10,
        simple_start_from=1,
        base_url=HttpUrl("https://example.com"),
        element_url_pattern="/page/\\d+",
    )


@pytest.fixture()
def repo(tmp_path):
    file_path = tmp_path / "paginations.json"
    return JsonPaginationRepo(file_path)


def test_repo_initially_empty(repo):
    content = repo._file.read_text()
    assert json.loads(content) == []
    assert repo.get() == []


def test_add_and_get_all(repo):
    pag = create_sample_pagination()
    repo.add(pag)
    all_pages = repo.get()
    assert isinstance(all_pages, list)
    assert len(all_pages) == 1
    assert all_pages[0] == pag


def test_get_by_id(repo):
    pag = create_sample_pagination()
    repo.add(pag)
    found = repo.get(pag.id)
    assert found == pag
    assert repo.get(UUID("00000000-0000-0000-0000-000000000000")) is None


def test_update_existing(repo):
    pag = create_sample_pagination()
    repo.add(pag)
    updated = Pagination(
        id=pag.id,
        type=PaginationType.SIMPLE,
        url="https://example.com/page/{n}",
        limit=20,
        simple_start_from=1,
        base_url=HttpUrl("https://example.com"),
        element_url_pattern="/page/\\d+",
    )
    repo.add(updated)
    all_pages = repo.get()
    assert len(all_pages) == 1
    assert all_pages[0].limit == 20


def test_persistence_between_instances(tmp_path):
    file_path = tmp_path / "p.json"
    repo1 = JsonPaginationRepo(file_path)
    pag = create_sample_pagination()
    repo1.add(pag)
    repo2 = JsonPaginationRepo(file_path)
    all_pages = repo2.get()
    assert len(all_pages) == 1
    assert all_pages[0] == pag
