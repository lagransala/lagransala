import pytest
from pydantic import HttpUrl
from sqlmodel import Session, SQLModel, create_engine

from lagransala.schedule.domain import Venue


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def venue_fixture() -> Venue:
    return Venue(
        name="Test Venue",
        slug="test-venue",
        description="A test venue",
        address="123 Test Street",
        location_latitude=0.0,
        location_longitude=0.0,
        website=HttpUrl("http://example.com"),
    )
