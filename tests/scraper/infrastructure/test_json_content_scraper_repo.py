import json
from uuid import uuid4

import pytest
from pydantic import UUID4, HttpUrl

from lagransala.scraper.domain import ContentScraper
from lagransala.scraper.infrastructure import JsonContentScraperRepo


@pytest.fixture()
def sample_content_scraper(id: UUID4 | None = None) -> ContentScraper:
    """Helper to create a valid simple content_scraper"""
    if id is None:
        id = uuid4()
    return ContentScraper(venue_slug="test-venue", main_selector="main")


@pytest.fixture()
def repo(tmp_path) -> JsonContentScraperRepo:
    file_path = tmp_path / "content_scrapers.json"
    return JsonContentScraperRepo(file_path)


def test_repo_initially_empty(repo: JsonContentScraperRepo):
    content = repo._file.read_text()
    assert json.loads(content) == []
    assert repo.get() == []


def test_add_and_get_all(
    repo: JsonContentScraperRepo, sample_content_scraper: ContentScraper
):
    repo.add(sample_content_scraper)
    all_pages = repo.get()
    assert isinstance(all_pages, list)
    assert len(all_pages) == 1
    assert all_pages[0] == sample_content_scraper


def test_get_by_slug(
    repo: JsonContentScraperRepo, sample_content_scraper: ContentScraper
):
    repo.add(sample_content_scraper)
    found = repo.get("test-venue")
    assert found == sample_content_scraper
    assert repo.get("fake-venue") is None


def test_update_existing(
    repo: JsonContentScraperRepo, sample_content_scraper: ContentScraper
):
    repo.add(sample_content_scraper)
    updated = ContentScraper(venue_slug="test-venue", main_selector="#main")
    repo.add(updated)
    all_scrapers = repo.get()
    assert len(all_scrapers) == 1
    assert all_scrapers[0].main_selector == "#main"


def test_persistence_between_instances(
    tmp_path, sample_content_scraper: ContentScraper
):
    file_path = tmp_path / "p.json"
    repo1 = JsonContentScraperRepo(file_path)
    repo1.add(sample_content_scraper)
    repo2 = JsonContentScraperRepo(file_path)
    all_pages = repo2.get()
    assert len(all_pages) == 1
    assert all_pages[0] == sample_content_scraper


def test_get_with_invalid_json_raises_value_error(repo: JsonContentScraperRepo):
    # Test with malformed JSON syntax
    repo._file.write_text("[{]")
    with pytest.raises(ValueError):
        repo.get()

    # Test with valid JSON but data that fails Pydantic validation
    repo._file.write_text('[{"venue_slug": 123}]')
    with pytest.raises(ValueError):
        repo.get()
