import time
from pathlib import Path

import pytest
from pydantic import BaseModel

from lagransala.shared.application import cached, generate_key
from lagransala.shared.infrastructure import FileCacheBackend, MemoryCacheBackend


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

    key1 = generate_key(sample_func, (1,), {"b": "hello"})
    key2 = generate_key(sample_func, (1,), {"b": "hello"})
    assert key1 == key2


def test_generate_key_arg_order_insensitivity():
    """Test that keyword argument order doesn't change the key."""

    def sample_func(a: int, b: str, c: bool):
        pass

    key1 = generate_key(sample_func, (1,), {"b": "hello", "c": True})
    key2 = generate_key(sample_func, (1,), {"c": True, "b": "hello"})
    assert key1 == key2


def test_generate_key_arg_difference():
    """Test that different arguments produce different keys."""

    def sample_func(a: int, b: str):
        pass

    key1 = generate_key(sample_func, (1,), {"b": "hello"})
    key2 = generate_key(sample_func, (2,), {"b": "world"})
    assert key1 != key2


def test_generate_key_with_key_params():
    """Test that key_params correctly filters arguments."""

    def sample_func(a: int, b: str, c: bool = False):
        pass

    # Keys should be the same because only 'a' is considered
    key1 = generate_key(sample_func, (1,), {"b": "hello"}, key_params=["a"])
    key2 = generate_key(sample_func, (1,), {"b": "world"}, key_params=["a"])
    assert key1 == key2

    # Keys should be different because 'a' is different
    key3 = generate_key(sample_func, (2,), {"b": "world"}, key_params=["a"])
    assert key1 != key3

    # Keys should be the same because 'b' and 'c' are ignored
    key4 = generate_key(
        sample_func, (), {"a": 1, "b": "another", "c": True}, key_params=["a"]
    )
    assert key1 == key4


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


def test_cached_key_func_and_key_params_exclusive(memory_cache_backend):
    """Test that providing both key_func and key_params raises an error."""
    with pytest.raises(ValueError):

        @cached(
            backend=memory_cache_backend,
            key_func=lambda f, *a, **kw: "",
            key_params=["a"],
        )
        async def some_function(a: int) -> SimpleData:
            return SimpleData(value="test")


@pytest.mark.asyncio
async def test_cached_with_key_params(memory_cache_backend):
    """Test that the decorator correctly uses key_params to generate the key."""
    call_count = 0

    @cached(backend=memory_cache_backend, key_params=["a"])
    async def selective_keyed_function(a: int, b: str) -> SimpleData:
        nonlocal call_count
        call_count += 1
        return SimpleData(value=f"{a}-{b}")

    # First call
    await selective_keyed_function(1, "one")
    assert call_count == 1

    # Second call with same key_param, should be cached
    await selective_keyed_function(1, "two")
    assert call_count == 1

    # Third call with different key_param, should execute again
    await selective_keyed_function(2, "one")
    assert call_count == 2


@pytest.mark.asyncio
async def test_cached_with_custom_key_func(memory_cache_backend):
    """Test that the decorator uses a custom key function when provided."""
    call_count = 0

    def custom_key_func(func, *args, **kwargs):
        return f"custom::{func.__name__}::{args[0]}"

    @cached(backend=memory_cache_backend, key_func=custom_key_func)
    async def custom_keyed_function(a: int) -> SimpleData:
        nonlocal call_count
        call_count += 1
        return SimpleData(value=f"custom_{a}")

    # First call
    await custom_keyed_function(1)
    assert call_count == 1

    # Second call
    await custom_keyed_function(1)
    assert call_count == 1

    # Check the custom key in the cache
    custom_key = custom_key_func(custom_keyed_function, 1)
    cached_data = await memory_cache_backend.get(custom_key)
    assert cached_data is not None
    assert cached_data.value == "custom_1"
