from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl

from lagransala.applications.event_discovery import get_venue_pagination
from lagransala.scraper.domain import Pagination, PaginationRepo


def test_get_venue_pagination_found(venue) -> None:
    """Test that we can get a venue's pagination when it exists."""
    repo = MagicMock(spec=PaginationRepo)
    pagination = Pagination(
        venue_slug="test-venue",
        base_url=HttpUrl("http://example.com"),
        url="http://example.com",
        element_url_pattern=".*",
    )
    repo.get.return_value = pagination

    result = get_venue_pagination(repo, venue)

    assert result == pagination
    repo.get.assert_called_once_with("test-venue")


def test_get_venue_pagination_not_found(venue) -> None:
    """Test that a ValueError is raised when pagination is not found."""
    repo = MagicMock(spec=PaginationRepo)
    repo.get.return_value = None

    with pytest.raises(ValueError):
        get_venue_pagination(repo, venue)

    repo.get.assert_called_once_with("test-venue")
