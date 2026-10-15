from collections.abc import Callable, Coroutine
from typing import Any


async def coroutine_with_data[T, D, R](
    coroutine: Coroutine[Any, Any, T],
    data: D,
    combiner: Callable[[T, D], R],
) -> R:
    result = await coroutine
    return combiner(result, data)
