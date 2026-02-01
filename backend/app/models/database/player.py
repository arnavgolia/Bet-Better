"""Player database model."""

from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class Player(Base, UUIDMixin, TimestampMixin):
    """NFL/NBA player entity."""

    __tablename__ = "players"

    name = Column(String(100), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    position = Column(String(10), nullable=False, index=True)
    jersey_number = Column(String(3), nullable=True)

    # Injury tracking
    injury_status = Column(String(20), nullable=True)  # "out", "doubtful", "questionable", "healthy"
    injury_impact = Column(Float, nullable=True)  # 0.0-1.0

    # Relationships
    team = relationship("Team", back_populates="players")
    marginals = relationship("PlayerMarginal", back_populates="player")
