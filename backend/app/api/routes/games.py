"""
Games API routes.
Provides access to game schedules and details.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies.database import get_db
from app.models.database import Game, Team, Venue
from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID

router = APIRouter(prefix="/games", tags=["games"])


class TeamSummary(BaseModel):
    """Minimal team info for game response."""
    id: str
    name: str
    abbreviation: str
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v
    
    class Config:
        from_attributes = True


class VenueSummary(BaseModel):
    """Minimal venue info for game response."""
    id: str
    name: str
    city: str
    is_dome: bool
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v
    
    class Config:
        from_attributes = True


class GameResponse(BaseModel):
    """Game response schema."""
    id: str
    sport: str
    home_team: TeamSummary
    away_team: TeamSummary
    venue: VenueSummary | None = None
    commence_time: datetime
    status: str
    spread: float | None = None
    total: float | None = None
    temperature_f: int | None = None
    wind_mph: int | None = None
    precipitation_prob: float | None = None
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[GameResponse])
async def list_games(
    sport: str | None = None,
    status: str | None = None,
    upcoming: bool = Query(False, description="Only show upcoming games"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of games.
    
    Query Parameters:
    - sport: Filter by sport (NFL, NBA, etc.)
    - status: Filter by status (scheduled, live, final)
    - upcoming: Only show games that haven't started yet
    """
    query = select(Game).options(
        selectinload(Game.home_team),
        selectinload(Game.away_team),
        selectinload(Game.venue)
    )
    
    if sport:
        query = query.where(Game.sport == sport.upper())
    
    if status:
        query = query.where(Game.status == status.lower())
    
    if upcoming:
        query = query.where(Game.commence_time > datetime.now())
    
    query = query.order_by(Game.commence_time)
    
    result = await db.execute(query)
    games = result.scalars().all()
    
    return [
        GameResponse(
            id=str(game.id),
            sport=game.sport,
            home_team=TeamSummary.model_validate(game.home_team),
            away_team=TeamSummary.model_validate(game.away_team),
            venue=VenueSummary.model_validate(game.venue) if game.venue else None,
            commence_time=game.commence_time,
            status=game.status,
            spread=game.spread,
            total=game.total,
            temperature_f=game.temperature_f,
            wind_mph=game.wind_mph,
            precipitation_prob=game.precipitation_prob,
            created_at=game.created_at
        )
        for game in games
    ]


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific game by ID."""
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
            selectinload(Game.venue)
        )
        .where(Game.id == game_id)
    )
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return GameResponse(
        id=str(game.id),
        sport=game.sport,
        home_team=TeamSummary.model_validate(game.home_team),
        away_team=TeamSummary.model_validate(game.away_team),
        venue=VenueSummary.model_validate(game.venue) if game.venue else None,
        commence_time=game.commence_time,
        status=game.status,
        spread=game.spread,
        total=game.total,
        temperature_f=game.temperature_f,
        wind_mph=game.wind_mph,
        precipitation_prob=game.precipitation_prob,
        created_at=game.created_at
    )
