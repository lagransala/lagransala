import time

import pytest
from pydantic import BaseModel

from lagransala.shared.infrastructure import MemoryCacheBackend


class SimpleData(BaseModel):
    name: str
    value: int


@pytest.fixture
def cache() -> MemoryCacheBackend[SimpleData]:
    return MemoryCacheBackend[SimpleData]()


@pytest.mark.asyncio
async def test_set_and_get(cache: MemoryCacheBackend[SimpleData]):
    """Test setting and getting a value."""
    key = "test_key"
    data = SimpleData(name="test", value=1)

    await cache.set(key, data)
    retrieved = await cache.get(key)

    assert retrieved == data


@pytest.mark.asyncio
async def test_get_non_existent(cache: MemoryCacheBackend[SimpleData]):
    """Test getting a non-existent key returns None."""
    assert await cache.get("non_existent_key") is None


@pytest.mark.asyncio
async def test_overwrite_value(cache: MemoryCacheBackend[SimpleData]):
    """Test that setting an existing key overwrites the value."""
    key = "overwrite_key"
    original_data = SimpleData(name="original", value=1)
    new_data = SimpleData(name="new", value=2)

    await cache.set(key, original_data)
    assert await cache.get(key) == original_data

    await cache.set(key, new_data)
    assert await cache.get(key) == new_data


@pytest.mark.asyncio
async def test_set_with_ttl(cache: MemoryCacheBackend[SimpleData]):
    """Test that a key with a TTL expires correctly."""
    key = "ttl_key"
    data = SimpleData(name="ttl_test", value=1)

    await cache.set(key, data, ttl=0.2)

    assert await cache.get(key) == data

    time.sleep(0.3)

    assert await cache.get(key) is None


@pytest.mark.asyncio
async def test_set_without_ttl(cache: MemoryCacheBackend[SimpleData]):
    """Test that a key without a TTL does not expire."""
    key = "no_ttl_key"
    data = SimpleData(name="no_ttl_test", value=1)

    await cache.set(key, data, ttl=None)

    time.sleep(1)  # Wait to ensure it would have expired if a short TTL was set

    assert await cache.get(key) == data
