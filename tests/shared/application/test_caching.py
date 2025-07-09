import time
from pathlib import Path

import pytest
from pydantic import BaseModel

from lagransala.shared.application.caching import cached, generate_key
from lagransala.shared.infrastructure.file_cache_backend import FileCacheBackend
from lagransala.shared.infrastructure.memory_cache_backend import MemoryCacheBackend


class SimpleData(BaseModel):
    value: str


# Fixtures for cache backends
@pytest.fixture
def memory_cache_backend() -> MemoryCacheBackend[SimpleData]:
    return MemoryCacheBackend[SimpleData]()


@pytest.fixture
def file_cache_backend(tmp_path: Path) -> FileCacheBackend[SimpleData]:
    cache_dir = tmp_path / "test_cache"
    return FileCacheBackend(data_type=SimpleData, cache_dir=str(cache_dir))


# Tests for generate_key
def test_generate_key_consistency():
    """Test that the same function and args produce the same key."""

    def sample_func(a: int, b: str):
        pass

    key1 = generate_key(sample_func, 1, b="hello")
    key2 = generate_key(sample_func, 1, b="hello")
    assert key1 == key2


def test_generate_key_arg_order_insensitivity():
    """Test that keyword argument order doesn't change the key."""

    def sample_func(a: int, b: str, c: bool):
        pass

    key1 = generate_key(sample_func, 1, b="hello", c=True)
    key2 = generate_key(sample_func, 1, c=True, b="hello")
    assert key1 == key2


def test_generate_key_arg_difference():
    """Test that different arguments produce different keys."""

    def sample_func(a: int, b: str):
        pass

    key1 = generate_key(sample_func, 1, b="hello")
    key2 = generate_key(sample_func, 2, b="world")
    assert key1 != key2


# Tests for the @cached decorator
@pytest.mark.asyncio
async def test_cached_with_memory_backend(memory_cache_backend):
    """Test that the decorator caches results using the memory backend."""
    call_count = 0

    @cached(backend=memory_cache_backend)
    async def expensive_function(a: int) -> SimpleData:
        nonlocal call_count
        call_count += 1
        return SimpleData(value=f"result_{a}")

    # First call, should execute the function
    result1 = await expensive_function(1)
    assert call_count == 1
    assert result1.value == "result_1"

    # Second call with same args, should be cached
    result2 = await expensive_function(1)
    assert call_count == 1  # Should not have increased
    assert result2.value == "result_1"

    # Call with different args, should execute again
    result3 = await expensive_function(2)
    assert call_count == 2
    assert result3.value == "result_2"


@pytest.mark.asyncio
async def test_cached_with_file_backend(file_cache_backend):
    """Test that the decorator caches results using the file backend."""
    call_count = 0

    @cached(backend=file_cache_backend)
    async def another_expensive_function(a: int, b: str) -> SimpleData:
        nonlocal call_count
        call_count += 1
        return SimpleData(value=f"{a}-{b}")

    # First call
    await another_expensive_function(1, "test")
    assert call_count == 1

    # Second call
    await another_expensive_function(1, "test")
    assert call_count == 1


@pytest.mark.asyncio
async def test_cached_with_ttl(memory_cache_backend):
    """Test that the cache expires after the TTL."""
    call_count = 0

    @cached(backend=memory_cache_backend, ttl=1)  # 1-second TTL
    async def timed_function(a: int) -> SimpleData:
        nonlocal call_count
        call_count += 1
        return SimpleData(value=f"timed_{a}")

    # First call
    await timed_function(1)
    assert call_count == 1

    # Second call (within TTL)
    await timed_function(1)
    assert call_count == 1

    # Wait for TTL to expire
    time.sleep(1.5)

    # Third call (after TTL), should execute again
    await timed_function(1)
    assert call_count == 2
