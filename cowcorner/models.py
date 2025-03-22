from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, String
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


FORMATS = Enum("Test", "First Class", "ODI", "T20I", "T20 Domestic", name="format")


class Game(Base, UpdatesTrackedMixin):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    date = Column(Date)
    format = Column(FORMATS)

    ground_id = Column(UUID(as_uuid=True), ForeignKey("grounds.id"))
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))

    ground = relationship("Ground", back_populates="games")
    home_team = relationship(
        "Team", back_populates="home_games", foreign_keys=[home_team_id]
    )
    away_team = relationship(
        "Team", back_populates="away_games", foreign_keys=[away_team_id]
    )


class Team(Base, UpdatesTrackedMixin):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), unique=True, nullable=False)

    home_games = relationship(
        "Game", back_populates="home_team", foreign_keys="Game.home_team_id"
    )
    away_games = relationship(
        "Game", back_populates="away_team", foreign_keys="Game.away_team_id"
    )

    @property
    def games(self):
        return self.home_games + self.away_games


class Ground(Base, UpdatesTrackedMixin):
    __tablename__ = "grounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), nullable=False)
    country = Column(String(255))

    games = relationship("Game", back_populates="ground")


BATTING_HANDS = Enum("Left", "Right", name="batting_hand")
BOWLING_STYLES = Enum(
    "Leg Spin", "Off Spin", "Fast", "Medium", "Chinaman", name="bowling_style"
)


class Player(Base, UpdatesTrackedMixin):
    __tablename__ = "players"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name = Column(String(255), nullable=False)
    batting_hand = Column(BATTING_HANDS)
    bowling_style = Column(BOWLING_STYLES)

    deliveries_bowled = relationship("Delivery", foreign_keys="Delivery.bowler_id")
    deliveries_faced = relationship("Delivery", foreign_keys="Delivery.batsman_id")


class Delivery(Base, UpdatesTrackedMixin):
    __tablename__ = "deliveries"
