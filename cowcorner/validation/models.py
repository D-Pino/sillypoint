"""
NB: This module defines pydantic models that map 1-1 with the SQLAlchemy ORM models
that I have set up for use with the database. Using pydantic is helpful for validation,
but this approach introduces the obvious problem of having to keep the two in sync.

In practice, I would like to use something like https://github.com/fastapi/sqlmodel to avoid
this problem entirely. However ultimately, the goal of this exercise is for me to work with all
these different technologies, so for now I'm keeping it like this so I can play with pydantic and
SQLAlchemy separately.
"""

import math
from datetime import date, datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cowcorner.common import Format, Hand


class Game(BaseModel):
    game_date: date | None = None
    game_format: Format | None = None


class Team(BaseModel):
    name: str = Field(max_length=255)


class Ground(BaseModel):
    name: str = Field(max_length=255)
    country: str | None = Field(default=None, max_length=255)


class Player(BaseModel):
    name: str = Field(max_length=255)


class Delivery(BaseModel):
    source_id: int | None = Field(default=None, alias="id")
    innings: int | None = Field(default=None, ge=1, le=4, alias="inns")
    over: int | None = Field(default=None, ge=0)
    ball: int | None = Field(default=None, ge=0)

    fielder: str | None = Field(default=None, max_length=255)
    batsman_hand: Hand | None = Field(default=None, alias="batsmanHand")
    bowler_hand: Hand | None = Field(default=None, alias="bowlerHand")
    bowling_style: str | None = Field(default=None, max_length=255, alias="bowlerType")

    is_wicket: bool | None = None
    dismissal_type: str | None = Field(
        default=None, max_length=255, alias="dismissalType"
    )

    line: str | None = Field(default=None, max_length=255)
    length: str | None = Field(default=None, max_length=255)
    variation: str | None = Field(default=None, max_length=255)

    foot: str | None = Field(default=None, max_length=255)
    shot: str | None = Field(default=None, max_length=255)
    shot_type: str | None = Field(default=None, max_length=255)
    control: str | None = Field(default=None, max_length=255)
    shot_angle: float | None = Field(default=None, ge=0, le=360)
    shot_magnitude: float | None = Field(default=None, ge=0)

    fielding_position: str | None = Field(default=None, max_length=255)
    fielding_action: str | None = Field(
        default=None, max_length=255, alias="fielder_action"
    )

    runs: int | None = Field(default=None, ge=0)
    runs_scored: int | None = Field(default=None, ge=0)
    runs_conceded: int | None = Field(default=None, ge=0)
    extras: int | None = Field(default=None, ge=0)

    commentary: str | None = None
    delivered_at: datetime | None = Field(default=None, alias="timestamp")

    zone: str | None = None
    area: str | None = None
    len_var: str | None = Field(default=None, max_length=255, alias="len/var")
    year: int | None = None
    elevation: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def handle_nans(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if pd.isna(value):
                    data[key] = None
        return data

    @field_validator("year", mode="before")
    @classmethod
    def handle_known_null_values(cls, value: Any) -> int | None:
        if value == "-":
            return None
        return value
