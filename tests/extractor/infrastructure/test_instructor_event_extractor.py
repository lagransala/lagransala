from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from lagransala.extractor.domain import (
    EmptyReason,
    EventExtraction,
    SourcedContent,
)
from lagransala.extractor.domain.event_extractor import SourcedEventExtraction
from lagransala.extractor.domain.sourced_content import ContentFormat
from lagransala.extractor.infrastructure.instructor_event_extractor import (
    InstructorEventExtractor,
)
from lagransala.shared.infrastructure.memory_cache_backend import MemoryCacheBackend


@pytest.fixture
def mock_client():
    """Fixture for mocking the instructor client."""
    client = MagicMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_instructor_event_extractor_extract(mock_client):
    """Test that the extract method calls the client with the correct parameters."""
    extractor = InstructorEventExtractor(client=mock_client, model="test-model")
    content = SourcedContent(
        url=HttpUrl("https://example.com"),
        content="Some content",
        fmt=ContentFormat.MD,
    )

    expected_result = SourcedEventExtraction(
        source_url=HttpUrl("https://example.com"),
        events=[],
        empty_reason=EmptyReason.NO_EVENTS_FOUND,
        model="test-model",
        dt=datetime.now()
    )
    mock_client.chat.completions.create.return_value = expected_result

    result = await extractor.extract(content)
    result.dt = expected_result.dt  # Normalize datetime for comparison

    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args

    assert call_args.kwargs["model"] == "test-model"
    assert call_args.kwargs["messages"][1]["content"] == content.content
    assert "first_day" in call_args.kwargs["context"]
    assert result == expected_result


@pytest.mark.asyncio
async def test_instructor_event_extractor_with_cache_extract(mock_client):
    """Test that the extract method calls the client with the correct parameters."""

    cache_backend = MemoryCacheBackend[SourcedEventExtraction]()

    extractor = InstructorEventExtractor(
        client=mock_client, model="test-model", cache_backend=cache_backend
    )

    content = SourcedContent(
        url=HttpUrl("https://example.com"),
        content="Some content",
        fmt=ContentFormat.MD,
    )

    expected_result = SourcedEventExtraction(
        source_url=HttpUrl("https://example.com"),
        events=[],
        empty_reason=EmptyReason.NO_EVENTS_FOUND,
        model="test-model",
        dt=datetime.now()
    )
    mock_client.chat.completions.create.return_value = expected_result

    result = await extractor.extract(content)
    result.dt = expected_result.dt  # Normalize datetime for comparison

    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args

    assert call_args.kwargs["model"] == "test-model"
    assert call_args.kwargs["messages"][1]["content"] == content.content
    assert "first_day" in call_args.kwargs["context"]
    assert result == expected_result

    changed_result = EventExtraction(events=[], empty_reason=EmptyReason.ONLY_PAST)
    mock_client.chat.completions.create.return_value = changed_result

    result = await extractor.extract(content)

    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args

    assert call_args.kwargs["model"] == "test-model"
    assert call_args.kwargs["messages"][1]["content"] == content.content
    assert "first_day" in call_args.kwargs["context"]
    assert result == expected_result, "result was not cached correctly"
