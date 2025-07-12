import pytest
from pydantic import HttpUrl

from lagransala.schedule.domain import Venue


@pytest.fixture
def venue():
    return Venue(
        name="Test Venue",
        slug="test-venue",
        description="A great place for events.",
        address="123 Test St, Test City",
        location_latitude=40.7128,
        location_longitude=-74.0060,
        website=HttpUrl("https://example.com"),
        schedule_url=HttpUrl("https://example.com/schedule"),
    )
