"""
NB: This module defines pydantic models that map 1-1 with the SQLAlchemy ORM models
that I have set up for use with the database. Using pydantic is helpful for validation,
but this approach introduces the obvious problem of having to keep the two in sync.

In practice, I would like to use something like https://github.com/fastapi/sqlmodel to avoid
this problem entirely. However ultimately, the goal of this exercise is for me to work with all
these different technologies, so for now I'm keeping it like this so I can play with pydantic and
SQLAlchemy separately.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from cowcorner.common import Format, Hand


class UpdatesTrackedBase(BaseModel):
    """Mixin for tracking creation and update timestamps"""

    created_at: datetime | None = Field(
        default=None, alias="_created_at", description="Timestamp of record creation"
    )
    updated_at: datetime | None = Field(
        default=None, alias="_updated_at", description="Timestamp of last update"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


# Core Models ----------
class Ground(UpdatesTrackedBase):
    id: UUID | None = None
    name: str = Field(max_length=255)
    country: str | None = Field(default=None, max_length=255)


class Team(UpdatesTrackedBase):
    id: UUID | None = None
    name: str = Field(max_length=255)


class Player(UpdatesTrackedBase):
    id: UUID | None = None
    name: str = Field(max_length=255)


class Game(UpdatesTrackedBase):
    id: UUID | None = None
    game_date: date | None = None
    game_format: Format | None = Field(default=None)
    ground_id: UUID | None = None
    home_team_id: UUID | None = None
    away_team_id: UUID | None = None


class Delivery(UpdatesTrackedBase):
    id: UUID | None = None
    competition: str | None = Field(default=None, max_length=255)
    game_id: UUID | None = None
    innings: int | None = Field(default=None, ge=1)
    over: int | None = Field(default=None, ge=0)
    ball: int | None = Field(default=None, ge=0)

    # Team/Player References
    batting_team_id: UUID | None = None
    batsman_id: UUID | None = None
    bowling_team_id: UUID | None = None
    bowler_id: UUID | None = None
    dismissed_player_id: UUID | None = None

    # Player Attributes
    batsman_hand: Hand | None = None
    bowler_hand: Hand | None = None
    bowling_style: str | None = Field(default=None, max_length=255)

    # Delivery Characteristics
    line: str | None = Field(default=None, max_length=255)
    length: str | None = Field(default=None, max_length=255)
    variation: str | None = Field(default=None, max_length=255)

    # Batting Outcomes
    foot: str | None = Field(default=None, max_length=255)
    shot: str | None = Field(default=None, max_length=255)
    shot_type: str | None = Field(default=None, max_length=255)
    control: str | None = Field(default=None, max_length=255)
    shot_angle: float | None = Field(default=None, ge=0, le=360)
    shot_magnitude: float | None = Field(default=None, ge=0)

    # Fielding Outcomes
    fielding_position: str | None = Field(default=None, max_length=255)
    fielding_action: str | None = Field(default=None, max_length=255)

    # Wicket Information
    is_wicket: bool | None = None
    dismissal_type: str | None = Field(default=None, max_length=255)

    # Run Information
    runs: int | None = Field(default=None, ge=0)
    runs_scored: int | None = Field(default=None, ge=0)
    runs_conceded: int | None = Field(default=None, ge=0)
    extras: int | None = Field(default=None, ge=0)

    # Temporal Data
    delivered_at: datetime | None = None

    # Additional Metadata
    commentary: str | None = None
    fielder: str | None = Field(default=None, max_length=255)
    zone: str | None = None
    area: str | None = None
    len_var: str | None = Field(default=None, max_length=255)
    year: int | None = None
    elevation: str | None = Field(default=None, max_length=255)
