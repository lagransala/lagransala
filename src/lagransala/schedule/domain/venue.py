import re
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import HttpUrl, field_validator
from sqlmodel import Field, Relationship, SQLModel

from lagransala.shared.application import build_sqlmodel_type
from lagransala.shared.domain import Slug

logger = __import__("loguru").logger

if TYPE_CHECKING:
    from .event import Event


class Venue(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    events: list["Event"] = Relationship(back_populates="venue")

    name: str
    slug: Slug = Field(unique=True)
    description: str
    address: str
    location_latitude: float
    location_longitude: float
    website: HttpUrl = Field(sa_type=build_sqlmodel_type(HttpUrl))
    schedule_url: HttpUrl | None = Field(
        sa_type=build_sqlmodel_type(HttpUrl), default=None
    )

    @field_validator("slug")
    def validate_slug(cls, v):
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("Invalid slug format")
        return v

    @field_validator("website", "schedule_url", mode="before")
    def validate_urls(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return HttpUrl(v)
        return v
