"""
Comprehensive data seeding script
Fetches live games from The Odds API and generates realistic player props
"""

import asyncio
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.database import Team, Player, Game, PlayerMarginal, Venue
from scipy.stats import norm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ODDS_API_KEY = "9f112142a5f6e462f209ebd9b6d4b2af"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Sports to fetch
SPORTS = [
    ("americanfootball_nfl", "NFL"),
    ("basketball_nba", "NBA"),
    ("icehockey_nhl", "NHL"),
]

# Sample players by position for each sport
NFL_PLAYERS = {
    "QB": ["QB1", "QB2"],
    "RB": ["RB1", "RB2"],
    "WR": ["WR1", "WR2", "WR3"],
    "TE": ["TE1"],
}

NBA_PLAYERS = {
    "PG": ["PG1", "PG2"],
    "SG": ["SG1", "SG2"],
    "SF": ["SF1", "SF2"],
    "PF": ["PF1"],
    "C": ["C1"],
}

NHL_PLAYERS = {
    "C": ["C1", "C2"],
    "LW": ["LW1", "LW2"],
    "RW": ["RW1", "RW2"],
    "D": ["D1", "D2"],
    "G": ["G1"],
}


async def fetch_live_games(sport_key: str):
    """Fetch live games from The Odds API"""
    async with httpx.AsyncClient() as client:
        url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
            "dateFormat": "iso"
        }
        
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching {sport_key}: {e}")
            return []


async def seed_comprehensive_data():
    """Seed database with live games and generated player props"""
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        total_games = 0
        total_props = 0
        
        for sport_key, sport_name in SPORTS:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {sport_name}...")
            logger.info(f"{'='*60}")
            
            games_data = await fetch_live_games(sport_key)
            logger.info(f"Fetched {len(games_data)} games from API")
            
            for game_data in games_data[:5]:  # Limit to 5 games per sport
                try:
                    # Get or create teams
                    home_team_name = game_data.get("home_team")
                    away_team_name = game_data.get("away_team")
                    
                    # Home team
                    result = await session.execute(
                        select(Team).where(Team.name == home_team_name)
                    )
                    home_team = result.scalar_one_or_none()
                    if not home_team:
                        home_team = Team(
                            name=home_team_name,
                            abbreviation=home_team_name[:3].upper(),
                            city=home_team_name.split()[-1] if " " in home_team_name else home_team_name,
                            league=sport_name
                        )
                        session.add(home_team)
                        await session.flush()
                        logger.info(f"  Created team: {home_team_name}")
                    
                    # Away team
                    result = await session.execute(
                        select(Team).where(Team.name == away_team_name)
                    )
                    away_team = result.scalar_one_or_none()
                    if not away_team:
                        away_team = Team(
                            name=away_team_name,
                            abbreviation=away_team_name[:3].upper(),
                            city=away_team_name.split()[-1] if " " in away_team_name else away_team_name,
                            league=sport_name
                        )
                        session.add(away_team)
                        await session.flush()
                        logger.info(f"  Created team: {away_team_name}")
                    
                    # Extract odds
                    spread = None
                    total = None
                    if game_data.get("bookmakers"):
                        for bookmaker in game_data["bookmakers"]:
                            for market in bookmaker.get("markets", []):
                                if market["key"] == "spreads" and not spread:
                                    for outcome in market.get("outcomes", []):
                                        if outcome["name"] == home_team_name:
                                            spread = outcome.get("point")
                                            break
                                elif market["key"] == "totals" and not total:
                                    for outcome in market.get("outcomes", []):
                                        total = outcome.get("point")
                                        break
                    
                    # Check if game exists
                    result = await session.execute(
                        select(Game).where(
                            (Game.home_team_id == home_team.id) &
                            (Game.away_team_id == away_team.id) &
                            (Game.commence_time == datetime.fromisoformat(game_data["commence_time"].replace('Z', '+00:00')))
                        )
                    )
                    existing_game = result.scalar_one_or_none()
                    
                    if existing_game:
                        logger.info(f"  Game exists: {away_team_name} @ {home_team_name}")
                        game = existing_game
                    else:
                        # Create game
                        game = Game(
                            sport=sport_name,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            commence_time=datetime.fromisoformat(game_data["commence_time"].replace('Z', '+00:00')),
                            status="scheduled",
                            spread=spread,
                            total=total
                        )
                        session.add(game)
                        await session.flush()
                        total_games += 1
                        logger.info(f"  ✅ Created game: {away_team_name} @ {home_team_name}")
                    
                    # Create players for both teams if they don't exist
                    player_template = NFL_PLAYERS if sport_name == "NFL" else NBA_PLAYERS if sport_name == "NBA" else NHL_PLAYERS
                    
                    all_players = []
                    for team in [home_team, away_team]:
                        for position, player_names in player_template.items():
                            for player_name in player_names:
                                full_name = f"{team.abbreviation} {player_name}"
                                
                                result = await session.execute(
                                    select(Player).where(
                                        (Player.name == full_name) & (Player.team_id == team.id)
                                    )
                                )
                                player = result.scalar_one_or_none()
                                
                                if not player:
                                    player = Player(
                                        name=full_name,
                                        team_id=team.id,
                                        position=position,
                                        jersey_number=str(len(all_players) + 1)
                                    )
                                    session.add(player)
                                    await session.flush()
                                
                                all_players.append((player, position))
                    
                    # Create player props
                    stat_configs = {
                        "NFL": {
                            "QB": [("passing_yards", 250, 60), ("passing_tds", 2, 1.2), ("completions", 22, 5)],
                            "RB": [("rushing_yards", 75, 30), ("rushing_attempts", 16, 5), ("receptions", 3, 2)],
                            "WR": [("receiving_yards", 65, 28), ("receptions", 5, 2.5)],
                            "TE": [("receiving_yards", 45, 22), ("receptions", 4, 2)],
                        },
                        "NBA": {
                            "PG": [("points", 18, 7), ("assists", 7, 3), ("rebounds", 4, 2)],
                            "SG": [("points", 16, 6), ("three_pointers", 2.5, 1.5)],
                            "SF": [("points", 15, 6), ("rebounds", 6, 2.5)],
                            "PF": [("points", 14, 5), ("rebounds", 8, 3)],
                            "C": [("points", 12, 5), ("rebounds", 10, 3.5)],
                        },
                        "NHL": {
                            "C": [("points", 0.8, 0.4), ("shots", 3.5, 1.5)],
                            "LW": [("points", 0.7, 0.4), ("shots", 3, 1.5)],
                            "RW": [("points", 0.7, 0.4), ("shots", 3, 1.5)],
                            "D": [("points", 0.4, 0.3), ("shots", 2.5, 1.2)],
                            "G": [("saves", 28, 6)],
                        }
                    }
                    
                    for player, position in all_players[:8]:  # Limit to 8 players per game
                        if position in stat_configs.get(sport_name, {}):
                            for stat_type, mean, std_dev in stat_configs[sport_name][position]:
                                line = mean - 0.5
                                z_score = (line - mean) / std_dev
                                under_prob = norm.cdf(z_score)
                                over_prob = 1 - under_prob
                                
                                prop = PlayerMarginal(
                                    game_id=game.id,
                                    player_id=player.id,
                                    stat_type=stat_type,
                                    line=line,
                                    mean=mean,
                                    std_dev=std_dev,
                                    over_probability=over_prob,
                                    under_probability=under_prob,
                                    over_odds=-110.0,
                                    under_odds=-110.0
                                )
                                session.add(prop)
                                total_props += 1
                    
                except Exception as e:
                    logger.error(f"  Error processing game: {e}")
                    continue
        
        await session.commit()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ SEEDING COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"Total Games Created: {total_games}")
        logger.info(f"Total Player Props Created: {total_props}")
        logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(seed_comprehensive_data())
