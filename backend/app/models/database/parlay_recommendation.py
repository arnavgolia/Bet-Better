"""Parlay recommendation model."""

from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class ParlayRecommendation(Base, UUIDMixin, TimestampMixin):
    """Generated parlay recommendations with AI analysis."""

    __tablename__ = "parlay_recommendations"

    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    
    # Parlay details
    legs = Column(JSON, nullable=False)  # Array of leg objects
    num_legs = Column(Integer, nullable=False)
    
    # Probability analysis
    true_probability = Column(Float, nullable=False)
    implied_probability = Column(Float, nullable=False)
    correlation_multiplier = Column(Float, nullable=False)
    
    # Expected value
    ev_percentage = Column(Float, nullable=False)
    recommended = Column(String(20), nullable=False)  # "strong_bet", "bet", "skip", "avoid"
    
    # Odds
    fair_odds = Column(Float, nullable=False)  # What odds SHOULD be
    sportsbook_odds = Column(Float, nullable=True)  # What odds ARE
    sportsbook_name = Column(String(50), nullable=True)
    
    # AI explanation
    regime_detected = Column(String(20), nullable=True)  # "blowout", "shootout", "defensive"
    explanation_factors = Column(JSON, nullable=True)  # Array of factor objects
    
    # Performance tracking
    simulation_time_ms = Column(Float, nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)

    # Relationships
    game = relationship("Game", back_populates="parlays")
