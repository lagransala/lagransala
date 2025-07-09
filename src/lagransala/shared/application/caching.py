import functools
import hashlib
import json
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

from pydantic import BaseModel

from lagransala.shared.domain.caching import CacheBackend, Data

P = ParamSpec("P")
R = TypeVar("R", bound=BaseModel)


def generate_key(func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> str:
    """Generate a cache key from a function and its arguments."""
    # Get the fully qualified name of the function
    func_name = f"{func.__module__}.{func.__qualname__}"

    # Sort kwargs to ensure consistent key generation
    sorted_kwargs = sorted(kwargs.items())

    # Create a representation of the arguments
    key_data = {
        "func": func_name,
        "args": args,
        "kwargs": sorted_kwargs,
    }

    # Serialize to a JSON string and hash it for a clean, fixed-length key
    serialized_data = json.dumps(key_data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized_data).hexdigest()


def cached(
    backend: CacheBackend[R],
    ttl: int | None = None,
    key_func: Callable[..., str] = generate_key,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    """Cache the result of an async function."""

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = key_func(func, *args, **kwargs)

            cached_value = await backend.get(key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await backend.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
