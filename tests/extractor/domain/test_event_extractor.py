from datetime import datetime

from lagransala.extractor.domain.event_data import EventData
from lagransala.extractor.domain.event_extractor import (
    EmptyReason,
    EventExtractionResult,
)


def test_event_extraction_result_with_events():
    """Test that EventExtractionResult can be created with a list of events."""
    now = datetime.now()
    event = EventData(
        title="Test Event",
        description="A test event.",
        schedule=[now],
        tags=[],
    )
    result = EventExtractionResult(events=[event], empty_reason=None)
    assert result.events == [event]
    assert result.empty_reason is None


def test_event_extraction_result_empty_with_reason():
    """Test that EventExtractionResult can be created with an empty list of events and a reason."""
    result = EventExtractionResult(events=[], empty_reason=EmptyReason.NO_EVENTS_FOUND)
    assert result.events == []
    assert result.empty_reason == EmptyReason.NO_EVENTS_FOUND
