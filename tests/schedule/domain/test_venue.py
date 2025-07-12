from uuid import uuid4

import pytest
from pydantic import HttpUrl, ValidationError

from lagransala.schedule.domain.venue import Venue


@pytest.fixture
def valid_venue_data():
    return {
        "name": "Test Venue",
        "slug": "test-venue",
        "description": "A great place for events.",
        "address": "123 Test St, Test City",
        "location_latitude": 40.7128,
        "location_longitude": -74.0060,
        "website": HttpUrl("https://example.com"),
        "schedule_url": HttpUrl("https://example.com/schedule"),
    }


def test_venue_creation_with_valid_data(valid_venue_data):
    """Test that a Venue can be created with valid data."""
    venue = Venue.model_validate(valid_venue_data)
    for key, value in valid_venue_data.items():
        assert getattr(venue, key) == value


@pytest.mark.parametrize(
    "invalid_slug", ["Invalid Slug", "invalid_slug!", "-invalid-slug", "invalid-slug-"]
)
def test_venue_with_invalid_slug(valid_venue_data, invalid_slug):
    """Test that creating a Venue with an invalid slug raises a ValidationError."""
    with pytest.raises(ValidationError):
        Venue.model_validate({**valid_venue_data, "slug": invalid_slug})


def test_venue_with_invalid_website_url(valid_venue_data):
    """Test that creating a Venue with an invalid website URL raises a ValidationError."""
    with pytest.raises(ValidationError):
        Venue.model_validate({**valid_venue_data, "website": "not-a-url"})


def test_venue_with_invalid_schedule_url(valid_venue_data):
    """Test that creating a Venue with an invalid schedule URL raises a ValidationError."""
    with pytest.raises(ValidationError):
        Venue.model_validate({**valid_venue_data, "schedule_url": "not-a-url"})
