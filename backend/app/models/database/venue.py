"""Venue database model."""

from sqlalchemy import Column, String, Boolean, Float
from sqlalchemy.orm import relationship
from app.models.database.base import Base, UUIDMixin, TimestampMixin


class Venue(Base, UUIDMixin, TimestampMixin):
    """Stadium/Arena entity."""

    __tablename__ = "venues"

    name = Column(String(100), nullable=False, index=True)
    city = Column(String(50), nullable=False)
    state = Column(String(2), nullable=True)  # US state code
    country = Column(String(2), nullable=False, default="US")
    
    # Venue characteristics
    is_dome = Column(Boolean, nullable=False, default=False)
    is_retractable = Column(Boolean, nullable=False, default=False)
    surface_type = Column(String(20), nullable=True)  # "grass", "turf", "fieldturf"
    elevation_ft = Column(Float, nullable=True)  # Important for Denver, Mexico City
    
    # Coordinates for weather API
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Relationships
    games = relationship("Game", back_populates="venue")
