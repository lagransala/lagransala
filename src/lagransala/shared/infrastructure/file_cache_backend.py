import base64
import json
import time
from pathlib import Path
from typing import Generic, Type, TypeVar

import aiofiles
import aiofiles.os
from pydantic import BaseModel

Data = TypeVar("Data", bound=BaseModel)


class FileCacheBackend(Generic[Data]):
    def __init__(self, data_type: Type[Data], cache_dir: str):
        self.data_type = data_type
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        key = base64.urlsafe_b64encode(key.encode("utf-8")).decode("utf-8")
        return self.cache_dir / f"{key}.json"

    async def get(self, key: str) -> Data | None:
        path = self._path_for_key(key)
        if not await aiofiles.os.path.exists(path):
            return None
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
                payload = json.loads(content)

                expiry = payload.get("expiry")
                if expiry is not None and time.time() > expiry:
                    await aiofiles.os.remove(path)
                    return None

                return self.data_type.model_validate(payload["data"])
        except Exception:
            return None

    async def set(self, key: str, value: Data, ttl: int | None = None) -> None:
        path = self._path_for_key(key)
        expiry = (time.time() + ttl) if ttl is not None else None
        payload = {"expiry": expiry, "data": value.model_dump()}
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(payload))
