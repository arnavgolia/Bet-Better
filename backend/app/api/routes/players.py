"""
Players and Props API routes.
Provides access to player data and betting props.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies.database import get_db
from app.models.database import Player, PlayerMarginal, Team
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/players", tags=["players"])


class PlayerResponse(BaseModel):
    """Player response schema."""
    id: str
    name: str
    team_id: str
    team_name: str
    team_abbreviation: str
    position: str
    jersey_number: str | None = None
    injury_status: str | None = None
    injury_impact: float | None = None
    
    class Config:
        from_attributes = True


class PropBetResponse(BaseModel):
    """Player prop bet response."""
    id: str
    player_id: str
    player_name: str
    game_id: str
    stat_type: str
    line: float
    over_probability: float
    under_probability: float
    over_odds: float | None = None
    under_odds: float | None = None
    mean: float
    std_dev: float
    player: PlayerResponse | None = None
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[PlayerResponse])
async def list_players(
    team_id: str | None = None,
    position: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of players.
    
    Query Parameters:
    - team_id: Filter by team
    - position: Filter by position (QB, RB, WR, etc.)
    """
    query = select(Player).options(selectinload(Player.team))
    
    if team_id:
        query = query.where(Player.team_id == team_id)
    
    if position:
        query = query.where(Player.position == position.upper())
    
    query = query.order_by(Player.name)
    
    result = await db.execute(query)
    players = result.scalars().all()
    
    return [
        PlayerResponse(
            id=str(player.id),
            name=player.name,
            team_id=str(player.team_id),
            team_name=player.team.name,
            team_abbreviation=player.team.abbreviation,
            position=player.position,
            jersey_number=player.jersey_number,
            injury_status=player.injury_status,
            injury_impact=player.injury_impact
        )
        for player in players
    ]


@router.get("/game/{game_id}/props", response_model=List[PropBetResponse])
async def get_game_props(
    game_id: str,
    stat_type: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all player props for a specific game.
    
    Query Parameters:
    - stat_type: Filter by stat type (passing_yards, rushing_yards, etc.)
    """
    query = select(PlayerMarginal).options(
        selectinload(PlayerMarginal.player).selectinload(Player.team)
    ).where(PlayerMarginal.game_id == game_id)
    
    if stat_type:
        query = query.where(PlayerMarginal.stat_type == stat_type)
    
    query = query.order_by(PlayerMarginal.player_id, PlayerMarginal.stat_type)
    
    result = await db.execute(query)
    props = result.scalars().all()
    
    return [
        PropBetResponse(
            id=str(prop.id),
            player_id=str(prop.player_id),
            player_name=prop.player.name,
            game_id=str(prop.game_id),
            stat_type=prop.stat_type,
            line=prop.line,
            over_probability=prop.over_probability,
            under_probability=prop.under_probability,
            over_odds=prop.over_odds,
            under_odds=prop.under_odds,
            mean=prop.mean,
            std_dev=prop.std_dev,
            player=PlayerResponse(
                id=str(prop.player.id),
                name=prop.player.name,
                team_id=str(prop.player.team_id),
                team_name=prop.player.team.name,
                team_abbreviation=prop.player.team.abbreviation,
                position=prop.player.position,
                jersey_number=prop.player.jersey_number,
                injury_status=prop.player.injury_status,
                injury_impact=prop.player.injury_impact
            )
        )
        for prop in props
    ]


@router.get("/game/{game_id}/marginals", response_model=List[PropBetResponse])
async def get_game_marginals(
    game_id: str,
    stat_type: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get player marginals (projected stats) for a specific game.
    This is an alias for /props endpoint to match frontend expectations.
    
    Query Parameters:
    - stat_type: Filter by stat type (passing_yards, rushing_yards, etc.)
    """
    # Just call the props endpoint
    return await get_game_props(game_id, stat_type, db)


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific player by ID."""
    result = await db.execute(
        select(Player)
        .options(selectinload(Player.team))
        .where(Player.id == player_id)
    )
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return PlayerResponse(
        id=str(player.id),
        name=player.name,
        team_id=str(player.team_id),
        team_name=player.team.name,
        team_abbreviation=player.team.abbreviation,
        position=player.position,
        jersey_number=player.jersey_number,
        injury_status=player.injury_status,
        injury_impact=player.injury_impact
    )
