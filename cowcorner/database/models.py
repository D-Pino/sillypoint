from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base, relationship
from uuid_extensions import uuid7

Base = declarative_base()


# Mixin to keep track of created and updated timestamps, used in most of my models
class UpdatesTrackedMixin:
    @declared_attr
    def _created_at(cls):
        return Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )

    @declared_attr
    def _updated_at(cls):
        return Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        )


class Game(Base, UpdatesTrackedMixin):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    source_id = Column(Integer)

    game_date = Column(Date)
    competition = Column(String(255))
    game_format = Column(String(255))

    ground_id = Column(UUID(as_uuid=True), ForeignKey("grounds.id"))
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))

    ground = relationship("Ground", back_populates="games")
    deliveries = relationship("Delivery", back_populates="game")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home")
    away_team = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_games"
    )


class Team(Base, UpdatesTrackedMixin):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), unique=True, nullable=False)

    home_games = relationship(
        "Game", foreign_keys="Game.home_team_id", back_populates="home_team"
    )
    away_games = relationship(
        "Game", foreign_keys="Game.away_team_id", back_populates="away_team"
    )
    deliveries_faced = relationship(
        "Delivery",
        foreign_keys="Delivery.batting_team_id",
        back_populates="batting_team",
    )
    deliveries_bowled = relationship(
        "Delivery",
        foreign_keys="Delivery.bowling_team_id",
        back_populates="bowling_team",
    )

    @property
    def games(self):
        return self.home_games + self.away_games

    @property
    def deliveries(self):
        return self.deliveries_faced + self.deliveries_bowled


class Ground(Base, UpdatesTrackedMixin):
    __tablename__ = "grounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), unique=True, nullable=False)
    country = Column(String(255))

    games = relationship("Game", back_populates="ground")


class Player(Base, UpdatesTrackedMixin):
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), unique=True, nullable=False)

    # These could vary so I'm gna have to think a little more about how to represent these
    # batting_hand = Column(HANDS)
    # bowling_style = Column(BOWLING_STYLES)

    deliveries_bowled = relationship(
        "Delivery", foreign_keys="Delivery.bowler_id", back_populates="bowler"
    )
    deliveries_faced = relationship(
        "Delivery", foreign_keys="Delivery.batsman_id", back_populates="batsman"
    )
    dismissals = relationship(
        "Delivery",
        foreign_keys="Delivery.dismissed_player_id",
        back_populates="dismissed_player",
    )
    # TODO: Add games? Maybe this has to be via an association table? (good practice)


# TODO: Consider restricting some fields (bowling_style, dismissal_type, fielding positions etc) to Enums
class Delivery(Base, UpdatesTrackedMixin):
    __tablename__ = "deliveries"
    # I would like to add this constraint but the data has mistakes (not too many but some)
    # __table_args__ = (UniqueConstraint("game_id", "innings", "over", "ball", name="uq_delivery_position"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    source_id = Column(Integer, unique=True)

    # Game info
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"))
    innings = Column(Integer)
    over = Column(Integer)
    ball = Column(Integer)

    # Team / player info
    batting_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    batsman_id = Column(UUID(as_uuid=True), ForeignKey("players.id"))
    bowling_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    bowler_id = Column(UUID(as_uuid=True), ForeignKey("players.id"))
    fielder = Column(
        String(255)
    )  # would like this to be a foreign key but data only tracks last name
    batsman_hand = Column(String(255))
    bowler_hand = Column(String(255))
    bowling_style = Column(String(255))

    ## Results of delivery

    # Wicket
    is_wicket = Column(Boolean)
    dismissal_type = Column(String(255))
    dismissed_player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"))

    # Bowling results
    line = Column(String(255))
    length = Column(String(255))
    variation = Column(String(255))

    # Batting results
    foot = Column(String(255))
    shot = Column(String(255))
    shot_type = Column(String(255))
    control = Column(String(255))
    shot_angle = Column(
        Float
    )  # in degrees, and as of now could be an int but future-proofing with Float
    shot_magnitude = Column(Float)  # idek what this is

    # Fielding results
    fielding_position = Column(String(255))
    fielding_action = Column(String(255))

    # Runs
    runs = Column(Integer)  # not sure the difference between runs and runs_scored
    runs_scored = Column(Integer)
    runs_conceded = Column(Integer)
    extras = Column(Integer)

    # Extra info
    commentary = Column(Text)
    delivered_at = Column(DateTime(timezone=True))

    # Idk what these are tbh
    zone = Column(Text)
    area = Column(Text)
    len_var = Column(String(255))
    year = Column(Integer)
    elevation = Column(String(255))  # idk if this is for the shot or the fielding throw

    ## Relationships
    batting_team = relationship(
        "Team", foreign_keys=[batting_team_id], back_populates="deliveries_faced"
    )
    batsman = relationship(
        "Player", foreign_keys=[batsman_id], back_populates="deliveries_faced"
    )
    bowling_team = relationship(
        "Team", foreign_keys=[bowling_team_id], back_populates="deliveries_bowled"
    )
    bowler = relationship(
        "Player", foreign_keys=[bowler_id], back_populates="deliveries_bowled"
    )
    dismissed_player = relationship(
        "Player", foreign_keys=[dismissed_player_id], back_populates="dismissals"
    )
    game = relationship("Game", back_populates="deliveries")
