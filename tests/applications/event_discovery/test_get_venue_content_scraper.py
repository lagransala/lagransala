from unittest.mock import MagicMock

import pytest

from lagransala.applications.event_discovery import get_venue_content_scraper
from lagransala.scraper.domain import ContentScraper, ContentScraperRepo


def test_get_venue_content_scraper_found(venue) -> None:
    """Test that we can get a venue's content scraper when it exists."""
    repo = MagicMock(spec=ContentScraperRepo)
    content_scraper = ContentScraper(venue_slug="test-venue", main_selector="main")
    repo.get.return_value = content_scraper

    result = get_venue_content_scraper(repo, venue)

    assert result == content_scraper
    repo.get.assert_called_once_with("test-venue")


def test_get_venue_content_scraper_not_found(venue) -> None:
    """Test that a ValueError is raised when a content scraper is not found."""
    repo = MagicMock(spec=ContentScraperRepo)
    repo.get.return_value = None

    with pytest.raises(ValueError):
        get_venue_content_scraper(repo, venue)

    repo.get.assert_called_once_with("test-venue")
