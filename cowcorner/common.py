import os
from enum import StrEnum
from typing import Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Enums
class Format(StrEnum):
    TEST = "Test"
    FIRST_CLASS = "First Class Domestic"
    ONE_DAY_DOMESTIC = "One Day Domestic"
    ODI = "ODI"
    T20I = "T20 International"
    T20_DOMESTIC = "T20 Domestic"


class Hand(StrEnum):
    LEFT = "Left"
    RIGHT = "Right"


# Database utilities
DB_URL = f"postgresql://{os.getenv('ODATA_DB_USER')}:{os.getenv('ODATA_DB_PASSWORD')}@localhost:{os.getenv('ODATA_DB_PORT')}/{os.getenv('ODATA_DB_NAME')}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

# Helper functions
ModelType = TypeVar("ModelType", bound=DeclarativeBase)


def get_or_create(
    model: Type[ModelType], session: Session | None = None, **kwargs
) -> tuple[ModelType, bool]:
    if session is None:
        session = SessionLocal()
        created_session = True
    else:
        created_session = False

    # TODO: handle race conditions?
    found_model_instance = session.query(model).filter_by(**kwargs).one_or_none()
    if found_model_instance is not None:
        return found_model_instance, False

    # TODO: Add validation using my pydantic models?
    model_instance = model(**kwargs)
    session.add(model_instance)
    if created_session:
        session.commit()
        session.close()
    return model_instance, True
