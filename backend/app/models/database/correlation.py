"""Correlation database model."""

from sqlalchemy import Column, String, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class PlayerCorrelation(Base, UUIDMixin, TimestampMixin):
    """Pair-wise correlation coefficient between two player stats."""

    __tablename__ = "player_correlations"

    player_1_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    player_2_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    
    stat_1 = Column(String(30), nullable=False)  # e.g., "pass_yards"
    stat_2 = Column(String(30), nullable=False)  # e.g., "receiving_yards"
    
    correlation = Column(Float, nullable=False)  # Pearson correlation (-1.0 to 1.0)
    sample_size = Column(Float, nullable=True)   # Number of games used to calculate
    
    # Constraints and Indexes for fast lookup
    __table_args__ = (
        UniqueConstraint('player_1_id', 'stat_1', 'player_2_id', 'stat_2', name='uq_player_correlation'),
        Index('idx_correlation_lookup', 'player_1_id', 'player_2_id'),
    )
