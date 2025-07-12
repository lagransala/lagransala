import logging
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
from sqlmodel import Session, select

from ..domain import Venue

logger = logging.getLogger(__name__)


def seed_venues(session: Session, seed_path: Path | str):
    seed_path = seed_path if isinstance(seed_path, Path) else Path(seed_path)
    if session.exec(select(Venue)).first():
        logger.info("Venue table not empty, skipping seeding.")
        return
    logger.info("Seeding venues from %s", seed_path)

    adapter = TypeAdapter(list[Venue])
    with open(seed_path, "r") as file:
        try:
            venues = adapter.validate_json(file.read())
            for venue in venues:
                Venue.model_validate(venue)
        except ValidationError as e:
            for error in e.errors():
                logger.error(
                    "Error in %s: %s: %s", seed_path, error["loc"], error["msg"]
                )
            raise ValueError(f"Invalid JSON in {seed_path}: {e}") from e
    session.add_all(venues)
    session.commit()
