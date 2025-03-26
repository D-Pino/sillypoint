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
