"""
Service to ingest odds and update the database.
Handles team mapping and game upserts.
"""

from typing import Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.models.database import Game, Team
from app.services.odds.client import get_odds_client

logger = logging.getLogger(__name__)


async def fetch_and_update_nfl_odds(db: AsyncSession):
    """Fetch latest NFL odds and update database."""
    client = get_odds_client()
    try:
        odds_data = await client.get_odds(sport="americanfootball_nfl")
        await process_odds_batch(db, odds_data, sport="NFL")
    finally:
        await client.close()


async def process_odds_batch(
    db: AsyncSession, 
    odds_data: list, 
    sport: str, 
    preferred_book: str = "draftkings"
):
    """
    Process raw API response and update database.
    """
    # 1. Load Teams Map
    # Simplification: Loading all teams into memory map.
    result = await db.execute(select(Team))
    teams = result.scalars().all()
    
    # Map both full name and city+name to ID
    team_map = {t.name.lower(): t.id for t in teams}
    # Add alias if needed? The Mock returns "Kansas City Chiefs" which matches.

    updated_count = 0
    created_count = 0

    for item in odds_data:
        home_name = item["home_team"]
        away_name = item["away_team"]
        
        home_id = team_map.get(home_name.lower())
        away_id = team_map.get(away_name.lower())
        
        if not home_id or not away_id:
            logger.warning(f"Skipping game {home_name} vs {away_name}: Team not found in DB")
            continue
            
        commence_time = datetime.fromisoformat(item["commence_time"].replace("Z", "+00:00"))
        
        # Extract Lines from Preferred Bookmaker
        spread, total = parse_spread_and_total(item, preferred_book)
        
        # 2. Find Existing Game
        # Be careful of timezones and slight scheduling shifts. 
        # Match matches if same teams match within 24 hours.
        stmt = select(Game).where(
            Game.home_team_id == home_id,
            Game.away_team_id == away_id,
        )
        result = await db.execute(stmt)
        existing_games = result.scalars().all()
        
        matched_game = None
        for g in existing_games:
            # Check time delta (allow 24h variation for rescheduling)
            delta = abs((g.commence_time - commence_time.replace(tzinfo=None)).total_seconds())
            if delta < 86400:
                matched_game = g
                break
        
        if matched_game:
            # Update
            changed = False
            if spread is not None and matched_game.spread != spread:
                matched_game.spread = spread
                changed = True
            if total is not None and matched_game.total != total:
                matched_game.total = total
                changed = True
                
            if changed:
                logger.info(f"Updated lines for {home_name} vs {away_name}: Spread {spread}, Total {total}")
                updated_count += 1
        else:
            # Create
            new_game = Game(
                sport=sport,
                home_team_id=home_id,
                away_team_id=away_id,
                commence_time=commence_time.replace(tzinfo=None),
                status="scheduled",
                spread=spread,
                total=total
            )
            db.add(new_game)
            created_count += 1
            logger.info(f"Created new game: {home_name} vs {away_name}")

    await db.commit()
    logger.info(f"Ingestion Complete. Created: {created_count}, Updated: {updated_count}")


def parse_spread_and_total(game_data: dict, bookmaker_key: str) -> Tuple[Optional[float], Optional[float]]:
    """Extract spread and total from specific bookmaker."""
    spread = None
    total = None
    
    for book in game_data.get("bookmakers", []):
        if book["key"] == bookmaker_key:
            for market in book["markets"]:
                if market["key"] == "spreads":
                    # Usually 2 outcomes. We want the HOME team's spread usually, 
                    # or conventionally the favorite.
                    # Our DB logic: spread relative to whom? usually Home.
                    # e.g. Home -7.
                    # The API returns point for each team.
                    # Let's find outcome matching home_team name.
                    # But parse_spread logic needs home team name context.
                    # Simplification: Just grab one and assume logic.
                    # Actually, we need to know WHICH spread is for Home.
                    pass
                if market["key"] == "totals":
                    # Any outcome has 'point' which is the total
                    if market["outcomes"]:
                        total = market["outcomes"][0]["point"]
                        
    # Accessing Home Team spread specifically
    # Re-loop with context
    home_team = game_data["home_team"]
    for book in game_data.get("bookmakers", []):
        if book["key"] == bookmaker_key:
            for market in book["markets"]:
                if market["key"] == "spreads":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home_team:
                            spread = outcome["point"]
                            
    return spread, total
