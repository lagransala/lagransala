from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

Data = TypeVar("Data", bound=BaseModel)


class CacheBackend(Protocol, Generic[Data]):

    async def get(self, key: str) -> Data | None: ...

    async def set(self, key: str, value: Data, ttl: float | None = None) -> None: ...
