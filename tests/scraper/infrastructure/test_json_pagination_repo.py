import json
from uuid import uuid4

import pytest
from pydantic import UUID4, HttpUrl

from lagransala.scraper.domain import Pagination, PaginationType
from lagransala.scraper.infrastructure import JsonPaginationRepo


@pytest.fixture()
def sample_pagination(id: UUID4 | None = None) -> Pagination:
    """Helper to create a valid simple pagination"""
    if id is None:
        id = uuid4()
    return Pagination(
        venue_slug="test-venue",
        type=PaginationType.SIMPLE,
        url="https://example.com/page/{n}",
        limit=10,
        simple_start_from=1,
        base_url=HttpUrl("https://example.com"),
        element_url_pattern="/page/\\d+",
    )


@pytest.fixture()
def repo(tmp_path) -> JsonPaginationRepo:
    file_path = tmp_path / "paginations.json"
    return JsonPaginationRepo(file_path)


def test_repo_initially_empty(repo: JsonPaginationRepo):
    content = repo._file.read_text()
    assert json.loads(content) == []
    assert repo.get() == []


def test_add_and_get_all(repo: JsonPaginationRepo, sample_pagination: Pagination):
    repo.add(sample_pagination)
    all_pages = repo.get()
    assert isinstance(all_pages, list)
    assert len(all_pages) == 1
    assert all_pages[0] == sample_pagination


def test_get_by_slug(repo: JsonPaginationRepo, sample_pagination: Pagination):
    repo.add(sample_pagination)
    found = repo.get("test-venue")
    assert found == sample_pagination
    assert repo.get("fake-venue") is None


def test_update_existing(repo: JsonPaginationRepo, sample_pagination: Pagination):
    repo.add(sample_pagination)
    updated = Pagination(
        venue_slug="test-venue",
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


def test_persistence_between_instances(tmp_path, sample_pagination: Pagination):
    file_path = tmp_path / "p.json"
    repo1 = JsonPaginationRepo(file_path)
    repo1.add(sample_pagination)
    repo2 = JsonPaginationRepo(file_path)
    all_pages = repo2.get()
    assert len(all_pages) == 1
    assert all_pages[0] == sample_pagination


def test_get_with_invalid_json_raises_value_error(repo: JsonPaginationRepo):
    # Test with malformed JSON syntax
    repo._file.write_text("[{]")
    with pytest.raises(ValueError):
        repo.get()

    # Test with valid JSON but data that fails Pydantic validation
    repo._file.write_text('[{"venue_slug": 123}]')
    with pytest.raises(ValueError):
        repo.get()
