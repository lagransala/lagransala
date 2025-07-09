import functools
import hashlib
import inspect
import json
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, TypeVar

from pydantic import BaseModel

from lagransala.shared.domain.caching import CacheBackend, Data

P = ParamSpec("P")
R = TypeVar("R", bound=BaseModel)


def generate_key(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_params: list[str] | None = None,
) -> str:
    """Generate a cache key from a function and its arguments."""
    # Get the fully qualified name of the function
    func_name = f"{func.__module__}.{func.__qualname__}"

    sig = inspect.signature(func)
    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()

    if key_params:
        filtered_args = {}
        for param_name in key_params:
            if param_name in bound_args.arguments:
                filtered_args[param_name] = bound_args.arguments[param_name]
        key_data = {"func": func_name, "kwargs": sorted(filtered_args.items())}
    else:
        key_data = {
            "func": func_name,
            "args": bound_args.args,
            "kwargs": sorted(bound_args.kwargs.items()),
        }

    # Serialize to a JSON string and hash it for a clean, fixed-length key
    serialized_data = json.dumps(key_data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized_data).hexdigest()


def cached(
    backend: CacheBackend[R],
    ttl: float | None = None,
    key_func: Callable[Concatenate[Callable[P, Any], P], str] | None = None,
    key_params: list[str] | None = None,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    """Cache the result of an async function."""

    if key_func and key_params:
        raise ValueError("key_func and key_params are mutually exclusive")

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if key_func:
                key = key_func(func, *args, **kwargs)
            else:
                key = generate_key(func, args, kwargs, key_params=key_params)

            cached_value = await backend.get(key)
            if cached_value is not None:
                # func_name = f"{func.__module__}.{func.__qualname__}"
                # print(f"Cache hit for {func_name}({args}, {kwargs})")
                return cached_value

            result = await func(*args, **kwargs)
            await backend.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
