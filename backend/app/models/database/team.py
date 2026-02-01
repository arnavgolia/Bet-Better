"""Team database model."""

from sqlalchemy import Column, String, Float
from sqlalchemy.orm import relationship
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class Team(Base, UUIDMixin, TimestampMixin):
    """NFL/NBA team entity."""

    __tablename__ = "teams"

    name = Column(String(100), nullable=False, index=True)
    abbreviation = Column(String(5), nullable=False, unique=True, index=True)
    city = Column(String(50), nullable=False)
    league = Column(String(10), nullable=False, index=True)  # "NFL", "NBA"

    # Advanced metrics (updated weekly)
    offensive_dvoa = Column(Float, nullable=True)
    defensive_dvoa = Column(Float, nullable=True)

    # Relationships
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")
