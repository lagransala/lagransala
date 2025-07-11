import functools
import hashlib
import inspect
import json
import logging
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, TypeVar

from pydantic import BaseModel

from lagransala.shared.domain.caching import CacheBackend, Data

P = ParamSpec("P")
R = TypeVar("R", bound=BaseModel)

logger = logging.getLogger(__name__)


def _get_filtered_args(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_params: list[str] | None,
) -> dict[str, Any]:
    """Bind arguments to the function signature and filter them based on key_params."""
    sig = inspect.signature(func)
    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()

    if not key_params:
        return bound_args.arguments

    filtered_args = {}
    for param_name in key_params:
        if param_name in bound_args.arguments:
            filtered_args[param_name] = bound_args.arguments[param_name]
    return filtered_args


def generate_key(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    key_params: list[str] | None = None,
) -> str:
    """Generate a cache key from a function and its arguments."""
    func_name = f"{func.__module__}.{func.__qualname__}"

    relevant_args = _get_filtered_args(func, args, kwargs, key_params)

    # If key_params are not specified, the key is based on all args and kwargs
    if not key_params:
        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
        key_data = {
            "func": func_name,
            "args": bound_args.args,
            "kwargs": sorted(bound_args.kwargs.items()),
        }
    else:
        key_data = {"func": func_name, "kwargs": sorted(relevant_args.items())}

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
                func_name = f"{func.__module__}.{func.__qualname__}"
                log_params = _get_filtered_args(func, args, kwargs, key_params)
                params_str = ", ".join(f"{k}={v!r}" for k, v in log_params.items())
                logger.info("Cache hit for %s(%s)", func_name, params_str)
                return cached_value

            result = await func(*args, **kwargs)
            await backend.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
