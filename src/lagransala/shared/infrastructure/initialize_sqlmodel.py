from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine


def initialize_sqlmodel(db_uri: str) -> Engine:
    engine = create_engine(
        db_uri,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    return engine
