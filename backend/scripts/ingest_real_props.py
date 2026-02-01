"""
Fetch real player props from The Odds API
Includes FanDuel, DraftKings, and other bookmakers
"""

import asyncio
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.database import Team, Player, Game, PlayerMarginal
from scipy.stats import norm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ODDS_API_KEY = "9f112142a5f6e462f209ebd9b6d4b2af"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Player prop markets to fetch
PLAYER_PROP_MARKETS = {
    "NFL": [
        "player_pass_yds",
        "player_pass_tds",
        "player_rush_yds",
        "player_reception_yds",
        "player_receptions",
    ],
    "NBA": [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_threes",
    ],
    "NHL": [
        "player_points",
        "player_shots_on_goal",
    ]
}

# Map API stat types to our database stat types
STAT_TYPE_MAP = {
    "player_pass_yds": "passing_yards",
    "player_pass_tds": "passing_tds",
    "player_rush_yds": "rushing_yards",
    "player_reception_yds": "receiving_yards",
    "player_receptions": "receptions",
    "player_points": "points",
    "player_rebounds": "rebounds",
    "player_assists": "assists",
    "player_threes": "three_pointers",
    "player_shots_on_goal": "shots",
}


async def fetch_player_props(sport_key: str, event_id: str, market: str):
    """Fetch player props for a specific event and market"""
    async with httpx.AsyncClient() as client:
        url = f"{ODDS_API_BASE}/sports/{sport_key}/events/{event_id}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": market,
            "oddsFormat": "american",
            "bookmakers": "fanduel,draftkings"  # Focus on major bookmakers
        }
        
        try:
            response = await client.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching {market} for {event_id}: {e}")
            return None


async def ingest_real_player_props():
    """Fetch real player props from The Odds API and populate database"""
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Get all games
        result = await session.execute(select(Game))
        games = list(result.scalars().all())
        
        logger.info(f"Found {len(games)} games in database")
        
        # For demo purposes, we'll fetch live games from API first
        # Then match them to our database games
        
        sports_map = {
            "NFL": "americanfootball_nfl",
            "NBA": "basketball_nba",
            "NHL": "icehockey_nhl"
        }
        
        total_props_created = 0
        
        for sport_name, sport_key in sports_map.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Fetching {sport_name} games...")
            logger.info(f"{'='*60}")
            
            # First, get list of events
            async with httpx.AsyncClient() as client:
                url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
                params = {
                    "apiKey": ODDS_API_KEY,
                    "regions": "us",
                    "markets": "h2h",
                    "oddsFormat": "american"
                }
                
                try:
                    response = await client.get(url, params=params, timeout=10.0)
                    response.raise_for_status()
                    events = response.json()
                except Exception as e:
                    logger.error(f"Error fetching {sport_name} events: {e}")
                    continue
            
            logger.info(f"Found {len(events)} live {sport_name} events")
            
            # Process first 3 events to conserve API quota
            for event in events[:3]:
                event_id = event.get("id")
                home_team = event.get("home_team")
                away_team = event.get("away_team")
                
                logger.info(f"\n  Event: {away_team} @ {home_team}")
                
                # Find or create game in database
                result = await session.execute(
                    select(Game).where(
                        (Game.home_team.has(name=home_team)) &
                        (Game.away_team.has(name=away_team))
                    )
                )
                game = result.scalar_one_or_none()
                
                if not game:
                    logger.info(f"    Game not in database, skipping...")
                    continue
                
                # Fetch player props for each market
                for market in PLAYER_PROP_MARKETS.get(sport_name, []):
                    logger.info(f"    Fetching {market}...")
                    
                    props_data = await fetch_player_props(sport_key, event_id, market)
                    
                    if not props_data or not props_data.get("bookmakers"):
                        logger.info(f"      No data available")
                        continue
                    
                    # Process bookmaker data
                    for bookmaker in props_data["bookmakers"]:
                        bookmaker_name = bookmaker.get("key", "unknown")
                        
                        for market_data in bookmaker.get("markets", []):
                            if market_data.get("key") != market:
                                continue
                            
                            # Process each player outcome
                            for outcome in market_data.get("outcomes", []):
                                player_name = outcome.get("description")  # Player name
                                line = outcome.get("point")  # The line (e.g., 250.5 yards)
                                odds = outcome.get("price")  # American odds
                                
                                if not player_name or line is None:
                                    continue
                                
                                # Find or create player
                                result = await session.execute(
                                    select(Player).where(
                                        Player.name.ilike(f"%{player_name.split()[-1]}%")  # Match by last name
                                    ).limit(1)
                                )
                                player = result.scalar_one_or_none()
                                
                                if not player:
                                    # Create generic player
                                    # Get team for this player (home or away based on context)
                                    team_id = game.home_team_id  # Default to home team
                                    
                                    player = Player(
                                        name=player_name,
                                        team_id=team_id,
                                        position="UNKNOWN",
                                        jersey_number="0"
                                    )
                                    session.add(player)
                                    await session.flush()
                                    logger.info(f"      Created player: {player_name}")
                                
                                # Check if prop already exists
                                stat_type = STAT_TYPE_MAP.get(market, market)
                                result = await session.execute(
                                    select(PlayerMarginal).where(
                                        (PlayerMarginal.game_id == game.id) &
                                        (PlayerMarginal.player_id == player.id) &
                                        (PlayerMarginal.stat_type == stat_type)
                                    )
                                )
                                existing_prop = result.scalar_one_or_none()
                                
                                if existing_prop:
                                    continue
                                
                                # Estimate mean and std_dev from the line
                                # Assume line is set at mean - 0.5 * std_dev
                                mean = line + 5  # Rough estimate
                                std_dev = 25 if "yds" in market or "yards" in market else 5
                                
                                # Calculate probabilities
                                z_score = (line - mean) / std_dev
                                under_prob = norm.cdf(z_score)
                                over_prob = 1 - under_prob
                                
                                # Create prop
                                prop = PlayerMarginal(
                                    game_id=game.id,
                                    player_id=player.id,
                                    stat_type=stat_type,
                                    line=line,
                                    mean=mean,
                                    std_dev=std_dev,
                                    over_probability=over_prob,
                                    under_probability=under_prob,
                                    over_odds=odds if outcome.get("name") == "Over" else -110.0,
                                    under_odds=odds if outcome.get("name") == "Under" else -110.0
                                )
                                session.add(prop)
                                total_props_created += 1
                                logger.info(f"      ✅ {player_name}: {stat_type} O/U {line} ({bookmaker_name})")
                    
                    await session.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ REAL PLAYER PROPS INGESTED!")
        logger.info(f"Total Props Created: {total_props_created}")
        logger.info(f"Data Source: The Odds API (FanDuel, DraftKings)")
        logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(ingest_real_player_props())
