from unittest.mock import patch

from sqlalchemy import inspect
from sqlmodel import Field, SQLModel

from lagransala.shared.infrastructure.initialize_sqlmodel import initialize_sqlmodel


class DummyModel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


def test_initialize_sqlmodel() -> None:
    db_uri = "sqlite:///:memory:"

    with patch("sqlmodel.SQLModel.metadata.create_all") as mock_create_all:
        engine = initialize_sqlmodel(db_uri)

    mock_create_all.assert_called_once_with(engine)

    # A more integrated test to ensure it actually works
    engine = initialize_sqlmodel(db_uri)
    inspector = inspect(engine)
    assert "dummymodel" in inspector.get_table_names()
