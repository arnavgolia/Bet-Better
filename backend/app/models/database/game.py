"""Game database model."""

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class Game(Base, UUIDMixin, TimestampMixin):
    """Individual game/match entity."""

    __tablename__ = "games"

    sport = Column(String(10), nullable=False, index=True)
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    commence_time = Column(DateTime, nullable=False, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled, live, final, postponed

    # Betting lines (for quick access)
    spread = Column(Float, nullable=True)
    total = Column(Float, nullable=True)

    # Weather (if applicable)
    temperature_f = Column(Integer, nullable=True)
    wind_mph = Column(Integer, nullable=True)
    precipitation_prob = Column(Float, nullable=True)

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    venue = relationship("Venue", back_populates="games")
    parlays = relationship("ParlayRecommendation", back_populates="game")
