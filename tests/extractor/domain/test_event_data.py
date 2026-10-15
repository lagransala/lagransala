from datetime import datetime, timedelta

from lagransala.extractor.domain.event_data import EventData


def test_event_data_creation():
    """Test that EventData can be created with valid data."""
    now = datetime.now()
    event = EventData(
        title="Test Event",
        description="A test event.",
        author="Test Author",
        schedule=[now],
        duration=timedelta(hours=1),
    )
    assert event.title == "Test Event"
    assert event.description == "A test event."
    assert event.author == "Test Author"
    assert event.schedule == [now]
    assert event.duration == timedelta(hours=1)


def test_event_data_defaults():
    """Test that EventData can be created with default values."""
    event = EventData(
        title="Test Event",
        description="A test event.",
        author=None,
        schedule=[datetime.now()],
    )
    assert event.duration is None
    assert event.author is None
