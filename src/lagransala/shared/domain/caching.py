from typing import Protocol

from pydantic import BaseModel


class CacheBackend[Data: BaseModel](Protocol):
    async def get(self, key: str) -> Data | None: ...

    async def set(self, key: str, value: Data, ttl: float | None = None) -> None: ...
