"""Player marginal probability model."""

from sqlalchemy import Column, String, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class PlayerMarginal(Base, UUIDMixin, TimestampMixin):
    """Individual player prop marginal probabilities."""

    __tablename__ = "player_marginals"

    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    stat_type = Column(String(30), nullable=False, index=True)  # "passing_yards", "rushing_yards", etc.
    
    # Distribution parameters
    mean = Column(Float, nullable=False)
    std_dev = Column(Float, nullable=False)
    
    # Betting line
    line = Column(Float, nullable=False)
    over_probability = Column(Float, nullable=False)
    under_probability = Column(Float, nullable=False)
    
    # Sportsbook odds
    over_odds = Column(Float, nullable=True)  # American odds, e.g., +110
    under_odds = Column(Float, nullable=True)
    
    # Data source
    source = Column(String(50), nullable=False, default="model")  # "model", "odds_api", "manual"

    # Relationships
    player = relationship("Player", back_populates="marginals")
    game = relationship("Game")

    __table_args__ = (
        Index("idx_player_game_stat", "player_id", "game_id", "stat_type"),
    )
