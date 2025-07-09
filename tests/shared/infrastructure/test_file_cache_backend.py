import time
from pathlib import Path
from re import S

import pytest
from pydantic import BaseModel

from lagransala.shared.infrastructure import FileCacheBackend


class SimpleData(BaseModel):
    name: str
    value: int


class ComplexData(BaseModel):
    id: int
    user: SimpleData
    tags: list[str]


@pytest.fixture
def cache_simple(tmp_path: Path) -> FileCacheBackend[SimpleData]:
    cache_dir = tmp_path / "cache"
    return FileCacheBackend(data_type=SimpleData, cache_dir=str(cache_dir))


@pytest.fixture
def cache_complex(tmp_path: Path) -> FileCacheBackend[ComplexData]:
    cache_dir = tmp_path / "cache"
    return FileCacheBackend(data_type=ComplexData, cache_dir=str(cache_dir))


@pytest.mark.asyncio
async def test_set_and_get_simple_data(cache_simple: FileCacheBackend[SimpleData]):
    """Test setting and getting a simple data model."""

    key = "test_key_1"
    data = SimpleData(name="test_name", value=123)

    await cache_simple.set(key, data)

    retrieved_data = await cache_simple.get(key)

    assert retrieved_data is not None
    assert isinstance(retrieved_data, SimpleData)
    assert retrieved_data.name == "test_name"
    assert retrieved_data.value == 123
    assert retrieved_data == data


@pytest.mark.asyncio
async def test_get_non_existent_key(cache_simple: FileCacheBackend[SimpleData]):
    """Test getting a non-existent key returns None."""

    key = "non_existent_key"

    assert await cache_simple.get(key) is None


@pytest.mark.asyncio
async def test_set_and_get_complex_data(cache_complex: FileCacheBackend[ComplexData]):
    """Test setting and getting a more complex data model."""

    key = "test_key_2"
    user_data = SimpleData(name="complex_user", value=456)
    data = ComplexData(id=1, user=user_data, tags=["tag1", "tag2"])

    await cache_complex.set(key, data)

    retrieved_data = await cache_complex.get(key)

    assert retrieved_data is not None
    assert isinstance(retrieved_data, ComplexData)
    assert retrieved_data.id == 1
    assert retrieved_data.user.name == "complex_user"
    assert retrieved_data.user.value == 456
    assert retrieved_data.tags == ["tag1", "tag2"]
    assert retrieved_data == data


@pytest.mark.asyncio
async def test_overwrite_existing_key(cache_simple: FileCacheBackend[SimpleData]):
    """Test that setting a value for an existing key overwrites the old value."""

    key = "overwrite_key"
    original_data = SimpleData(name="original", value=1)
    new_data = SimpleData(name="new", value=2)

    await cache_simple.set(key, original_data)
    retrieved_once = await cache_simple.get(key)
    assert retrieved_once == original_data

    await cache_simple.set(key, new_data)
    retrieved_twice = await cache_simple.get(key)
    assert retrieved_twice == new_data


@pytest.mark.asyncio
async def test_get_with_corrupted_file(cache_simple: FileCacheBackend[SimpleData]):
    """Test that get returns None if the cache file is corrupted."""
    key = "corrupted_key"

    # Manually create a corrupted file
    cache_file_path = cache_simple._path_for_key(key)
    cache_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file_path, "w", encoding="utf-8") as f:
        f.write("this is not valid json")

    retrieved_data = await cache_simple.get(key)

    assert retrieved_data is None


@pytest.mark.asyncio
async def test_set_with_ttl(cache_simple: FileCacheBackend[SimpleData]):
    """Test setting a key with a TTL and retrieving it before it expires."""

    key = "ttl_key"
    data = SimpleData(name="ttl_test", value=1)

    await cache_simple.set(key, data, ttl=0.2)

    retrieved_data = await cache_simple.get(key)
    assert retrieved_data == data

    time.sleep(0.3)

    expired_data = await cache_simple.get(key)
    assert expired_data is None


@pytest.mark.asyncio
async def test_set_without_ttl(cache_simple: FileCacheBackend[SimpleData]):
    """Test that a key set without a TTL does not expire."""
    key = "no_ttl_key"
    data = SimpleData(name="no_ttl_test", value=1)

    await cache_simple.set(key, data, ttl=None)

    time.sleep(0.5)  # Wait to ensure it would have expired if a short TTL was set

    retrieved_data = await cache_simple.get(key)
    assert retrieved_data == data
