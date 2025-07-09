from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from lagransala.extractor.domain.event_data import EventData


def test_event_data_creation():
    """Test that EventData can be created with valid data."""
    now = datetime.now()
    event = EventData(
        title="Test Event",
        description="A test event.",
        schedule=[now],
        duration=timedelta(hours=1),
        tags=["test", "event"],
        category="cine",
        price=Decimal("10.50"),
    )
    assert event.title == "Test Event"
    assert event.description == "A test event."
    assert event.schedule == [now]
    assert event.duration == timedelta(hours=1)
    assert event.tags == ["test", "event"]
    assert event.category == "cine"
    assert event.price == Decimal("10.50")


def test_event_data_defaults():
    """Test that EventData can be created with default values."""
    now = datetime.now()
    event = EventData(
        title="Test Event",
        description="A test event.",
        schedule=[now],
        tags=[],
    )
    assert event.duration is None
    assert event.category is None
    assert event.price is None


def test_event_data_invalid_price():
    """Test that EventData raises a validation error for an invalid price."""
    now = datetime.now()
    with pytest.raises(ValidationError):
        EventData(
            title="Test Event",
            description="A test event.",
            schedule=[now],
            tags=[],
            price=Decimal("10.555"),
        )


def test_event_data_invalid_category():
    """Test that EventData raises a validation error for an invalid category."""
    now = datetime.now()
    with pytest.raises(ValidationError):
        EventData(
            title="Test Event",
            description="A test event.",
            schedule=[now],
            tags=[],
            category="invalid_category",  # type: ignore
        )
