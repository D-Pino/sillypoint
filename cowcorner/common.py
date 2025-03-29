import os
from enum import StrEnum


class Format(StrEnum):
    TEST = "Test"
    FIRST_CLASS = "First Class"
    ODI = "ODI"
    T20I = "T20I"
    T20_DOMESTIC = "T20 Domestic"


class Hand(StrEnum):
    LEFT = "Left"
    RIGHT = "Right"


def get_db_url():
    return f"postgresql://{os.getenv('ODATA_DB_USER')}:{os.getenv('ODATA_DB_PASSWORD')}@localhost:{os.getenv('ODATA_DB_PORT')}/{os.getenv('ODATA_DB_NAME')}"
