from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class EventData(BaseModel):
    title: str
    description: str
    schedule: list[datetime]
    duration: timedelta | None = None
    tags: list[str] = Field(description="List of tags.")
    category: Literal["cine", "coloquio", "live_music"] | None = None
    price: Decimal | None = Field(
        default=None,
        max_digits=5,
        decimal_places=2,
        description="Price in euros. Dont include the euro sign, just a decimal with two digits after the comma.",
    )
