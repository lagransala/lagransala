import time
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

Data = TypeVar("Data", bound=BaseModel)


class MemoryCacheBackend(Generic[Data]):
    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    async def get(self, key: str) -> Data | None:
        entry = self._cache.get(key)
        if not entry:
            return None

        if entry["expiry"] is not None and time.time() > entry["expiry"]:
            del self._cache[key]
            return None

        return entry["value"]

    async def set(self, key: str, value: Data, ttl: float | None = None) -> None:
        expiry = (time.time() + ttl) if ttl is not None else None
        self._cache[key] = {"value": value, "expiry": expiry}
