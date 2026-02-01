"""
Teams API routes.
Provides access to team data.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies.database import get_db
from app.models.database import Team
from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamResponse(BaseModel):
    """Team response schema."""
    id: str
    name: str
    abbreviation: str
    city: str
    league: str
    offensive_dvoa: float | None = None
    defensive_dvoa: float | None = None
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        return str(v) if isinstance(v, UUID) else v
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[TeamResponse])
async def list_teams(
    league: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all teams.
    
    Query Parameters:
    - league: Filter by league (NFL, NBA, etc.)
    """
    query = select(Team)
    
    if league:
        query = query.where(Team.league == league.upper())
    
    query = query.order_by(Team.name)
    
    result = await db.execute(query)
    teams = result.scalars().all()
    
    return [TeamResponse.model_validate(team) for team in teams]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific team by ID."""
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return TeamResponse.model_validate(team)
