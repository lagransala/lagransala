import pytest
from sqlmodel import Session, select

from lagransala.schedule.application.seed_venues import seed_venues
from lagransala.schedule.domain import Venue


def test_seed_venues(session: Session):
    seed_venues(session, "seeds/venues.json")

    venues = session.exec(select(Venue)).all()
    assert len(venues) > 0
    assert venues[0].name == "Círculo de Bellas Artes"


def test_seed_venues_not_empty(session: Session, venue_fixture: Venue):
    session.add(venue_fixture)
    session.commit()

    seed_venues(session, "seeds/venues.json")

    venues = session.exec(select(Venue)).all()
    assert len(venues) == 1
    assert venues[0].name == venue_fixture.name


def test_seed_venues_invalid_json(session: Session, tmp_path):
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text(
        """
    [{
        "name": "Invalid Venue",
        "slug": "invalid-venue",
        "description": "desc",
        "address": "addr",
        "location_latitude": 0,
        "location_longitude": 0,
        "website": "not-a-url"
    }]
    """
    )

    with pytest.raises(ValueError, match="Invalid JSON"):
        seed_venues(session, invalid_json)


def test_seed_venues_file_not_found(session: Session):
    with pytest.raises(FileNotFoundError):
        seed_venues(session, "non_existent_file.json")
