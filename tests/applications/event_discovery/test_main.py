from unittest.mock import Mock, patch

import pytest
from pydantic import HttpUrl

from lagransala.applications.event_discovery.__main__ import State, main
from lagransala.extractor.domain import EmptyReason, EventExtractionResult
from lagransala.schedule.domain import Venue


@pytest.fixture
def mock_venue():
    return Venue(
        name="Test Venue",
        slug="test-venue",
        description="A test venue",
        address="123 Test St",
        location_latitude=40.7128,
        location_longitude=-74.0060,
        website=HttpUrl("http://test.com"),
    )


def test_state_with_content(mock_venue):
    state = State(url="http://test.com", venue=mock_venue)
    new_state = state.with_content("test content")
    assert new_state.content == "test content"
    assert new_state.venue == mock_venue


def test_state_with_extraction_result(mock_venue):
    state = State(url="http://test.com", venue=mock_venue)
    extraction_result = EventExtractionResult(
        events=[], empty_reason=EmptyReason.NO_EVENTS_FOUND
    )
    new_state = state.with_extraction_result(extraction_result)
    assert new_state.extraction_result == extraction_result
    assert new_state.venue == mock_venue


def test_state_md_content(mock_venue):
    state = State(
        url="http://test.com",
        venue=mock_venue,
        content="<html><body><main># Test</main></body></html>",
    )
    mock_repo = Mock()
    mock_scraper = Mock()
    mock_scraper.main_selector = "main"
    mock_repo.get_content_scraper.return_value = mock_scraper

    with patch(
        "lagransala.applications.event_discovery.__main__.get_venue_content_scraper"
    ) as mock_get_scraper:
        mock_get_scraper.return_value = mock_scraper
        md_content = state.md_content(mock_repo)
        assert md_content == "# Test"


@pytest.mark.asyncio
async def test_main_happy_path(mock_venue):
    with (
        patch(
            "lagransala.applications.event_discovery.__main__.initialize_sqlmodel"
        ) as mock_init_sql,
        patch(
            "lagransala.applications.event_discovery.__main__.Session"
        ) as mock_session,
        patch(
            "lagransala.applications.event_discovery.__main__.seed_venues"
        ) as mock_seed_venues,
        patch(
            "lagransala.applications.event_discovery.__main__.aiohttp.ClientSession"
        ) as mock_aiohttp_session,
        patch(
            "lagransala.applications.event_discovery.__main__.AiohttpFetcher"
        ) as mock_fetcher,
        patch(
            "lagransala.applications.event_discovery.__main__.JsonPaginationRepo"
        ) as mock_pagination_repo,
        patch(
            "lagransala.applications.event_discovery.__main__.pagination_elements"
        ) as mock_pagination_elements,
        patch(
            "lagransala.applications.event_discovery.__main__.instructor.from_litellm"
        ) as mock_instructor,
        patch(
            "lagransala.applications.event_discovery.__main__.InstructorEventExtractor"
        ) as mock_event_extractor,
        patch(
            "lagransala.applications.event_discovery.__main__.JsonContentScraperRepo"
        ) as mock_content_repo,
        patch(
            "lagransala.applications.event_discovery.__main__.asyncio.gather",
            new_callable=Mock,
        ) as mock_gather,
    ):

        # Setup mocks
        mock_session.return_value.__enter__.return_value.exec.return_value.all.return_value = [
            mock_venue
        ]
        mock_pagination_elements.return_value = ["http://test.com/page1"]

        # Mock the gather calls for fetching content and extracting events
        async def gather_side_effect(*args, **kwargs):
            return [Mock()]

        mock_gather.side_effect = gather_side_effect

        # Run the main function
        await main()

        # Assertions
        mock_init_sql.assert_called_once()
        mock_seed_venues.assert_called_once()
        mock_aiohttp_session.assert_called_once()
        mock_fetcher.assert_called_once()
        mock_pagination_repo.assert_called_once()
        mock_pagination_elements.assert_called_once()
        mock_instructor.assert_called_once()
        mock_event_extractor.assert_called_once()
        mock_content_repo.assert_called_once()
        assert mock_gather.call_count == 2
