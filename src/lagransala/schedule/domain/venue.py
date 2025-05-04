import logging
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import yaml
from pydantic import UUID4
from pydantic import Field as PydanticField
from pydantic import HttpUrl
from sqlmodel import Field, Relationship, Session, SQLModel, select

from lagransala.shared.application.build_sqlmodel_type import build_sqlmodel_type

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .event import Event


class Venue(SQLModel, table=True):
    id: UUID4 = Field(default_factory=uuid4, primary_key=True)

    events: list["Event"] = Relationship(back_populates="venue")

    name: str
    slug: str = PydanticField(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str
    address: str
    location_latitude: float
    location_longitude: float
    website: HttpUrl = Field(sa_type=build_sqlmodel_type(HttpUrl))
    schedule_url: HttpUrl | None = Field(sa_type=build_sqlmodel_type(HttpUrl))
