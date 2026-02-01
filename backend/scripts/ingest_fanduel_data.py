"""
Complete ingestion of REAL games and player props from The Odds API
Includes FanDuel, DraftKings, and other major bookmakers
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

# Sports to ingest
SPORTS = [
    ("americanfootball_nfl", "NFL"),
]

# Player prop markets
PROP_MARKETS = [
    "player_pass_yds",
    "player_pass_tds", 
    "player_rush_yds",
    "player_reception_yds",
    "player_anytime_td",
]

STAT_MAP = {
    "player_pass_yds": "passing_yards",
    "player_pass_tds": "passing_tds",
    "player_rush_yds": "rushing_yards",
    "player_reception_yds": "receiving_yards",
    "player_anytime_td": "anytime_tds",
}

# ESPN Team IDs map (The Odds API name -> ESPN ID)
ESPN_TEAM_IDS = {
    "Seattle Seahawks": "26",
    "New England Patriots": "17",
    "San Francisco 49ers": "25",
    "Kansas City Chiefs": "12",
    # Add more as needed or implement dynamic lookup
}


async def ingest_complete_data():
    """Fetch real games and player props from The Odds API"""
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        total_games = 0
        total_props = 0
        
        for sport_key, sport_name in SPORTS:
            logger.info(f"\n{'='*70}")
            logger.info(f"🏈 INGESTING {sport_name} DATA FROM THE ODDS API")
            logger.info(f"{'='*70}")
            
            # Fetch games with odds
            async with httpx.AsyncClient() as client:
                url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
                params = {
                    "apiKey": ODDS_API_KEY,
                    "regions": "us",
                    "markets": "h2h,spreads,totals",
                    "oddsFormat": "american"
                }
                
                try:
                    response = await client.get(url, params=params, timeout=10.0)
                    response.raise_for_status()
                    events = response.json()
                except Exception as e:
                    logger.error(f"Error fetching events: {e}")
                    continue
            
            logger.info(f"📡 Found {len(events)} live events\n")
            
            # Process each event
            for event in events[:5]:  # Limit to 5 to conserve API quota
                event_id = event.get("id")
                home_team_name = event.get("home_team")
                away_team_name = event.get("away_team")
                commence_time = datetime.fromisoformat(event.get("commence_time").replace('Z', '+00:00')).replace(tzinfo=None)
                
                logger.info(f"  🎮 {away_team_name} @ {home_team_name}")
                logger.info(f"     Time: {commence_time.strftime('%a, %b %d at %I:%M %p')}")
                
                # Get or create teams
                result = await session.execute(
                    select(Team).where(Team.name == home_team_name)
                )
                home_team = result.scalar_one_or_none()
                if not home_team:
                    home_team = Team(
                        name=home_team_name,
                        abbreviation=home_team_name.split()[-1][:3].upper(),
                        city=home_team_name.split()[0] if " " in home_team_name else home_team_name,
                        league=sport_name
                    )
                    session.add(home_team)
                    await session.flush()
                
                result = await session.execute(
                    select(Team).where(Team.name == away_team_name)
                )
                away_team = result.scalar_one_or_none()
                if not away_team:
                    away_team = Team(
                        name=away_team_name,
                        abbreviation=away_team_name.split()[-1][:3].upper(),
                        city=away_team_name.split()[0] if " " in away_team_name else away_team_name,
                        league=sport_name
                    )
                    session.add(away_team)
                    await session.flush()
                
                # Extract odds
                spread = None
                total = None
                if event.get("bookmakers"):
                    for bookmaker in event["bookmakers"]:
                        if bookmaker.get("key") in ["fanduel", "draftkings"]:
                            for market in bookmaker.get("markets", []):
                                if market["key"] == "spreads" and not spread:
                                    for outcome in market.get("outcomes", []):
                                        if outcome["name"] == home_team_name:
                                            spread = outcome.get("point")
                                elif market["key"] == "totals" and not total:
                                    total = market.get("outcomes", [{}])[0].get("point")
                
                # Create game
                game = Game(
                    sport=sport_name,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    commence_time=commence_time,
                    status="scheduled",
                    spread=spread,
                    total=total
                )
                session.add(game)
                await session.flush()
                total_games += 1
                
                logger.info(f"     Spread: {spread}, Total: {total}")
                logger.info(f"     ✅ Game created in database")
                
                # --- Fetch Rosters from ESPN (Heuristic Fix for Team Mapping) ---
                logger.info(f"     👥 Fetching rosters from ESPN to map players...")
                player_team_map = {}  # {normalized_name: team_id}
                
                espn_home_id = ESPN_TEAM_IDS.get(home_team_name)
                espn_away_id = ESPN_TEAM_IDS.get(away_team_name)
                
                async def fetch_roster(team_id, db_team_id):
                    if not team_id: return
                    try:
                        async with httpx.AsyncClient() as c:
                            r = await c.get(f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster")
                            data = r.json()
                            for grp in data.get('athletes', []):
                                for ath in grp.get('items', []):
                                    name = ath.get('fullName')
                                    if name:
                                        # Normalize: remove punctuation, lowercase
                                        norm = name.lower().replace('.', '').replace("'", "")
                                        player_team_map[norm] = db_team_id
                    except Exception as e:
                        logger.error(f"Error fetching ESPN roster for {team_id}: {e}")

                await asyncio.gather(
                    fetch_roster(espn_home_id, home_team.id),
                    fetch_roster(espn_away_id, away_team.id)
                )
                logger.info(f"     mapped {len(player_team_map)} players to teams")
                # -------------------------------------------------------------
                
                # Now fetch player props for this event
                logger.info(f"     📊 Fetching player props...")
                
                props_for_game = 0
                for market in PROP_MARKETS:
                    async with httpx.AsyncClient() as client:
                        url = f"{ODDS_API_BASE}/sports/{sport_key}/events/{event_id}/odds"
                        params = {
                            "apiKey": ODDS_API_KEY,
                            "regions": "us",
                            "markets": market,
                            "oddsFormat": "american",
                            "bookmakers": "fanduel"  # Focus on FanDuel
                        }
                        
                        try:
                            response = await client.get(url, params=params, timeout=15.0)
                            response.raise_for_status()
                            props_data = response.json()
                        except Exception as e:
                            logger.debug(f"       {market}: Not available")
                            continue
                    
                    if not props_data.get("bookmakers"):
                        continue
                    
                    # Process FanDuel data
                    for bookmaker in props_data["bookmakers"]:
                        for market_data in bookmaker.get("markets", []):
                                if "anytime" in market:
                                    n = outcome.get("name")
                                    d = outcome.get("description")
                                    if n in ["Yes", "Over"]:
                                         player_name = d
                                    else:
                                         player_name = n
                                    over_under = "Over"  # Implicitly "Over" 0.5
                                else:
                                    player_name = outcome.get("description")
                                    over_under = outcome.get("name")  # "Over" or "Under"
                                
                                line = outcome.get("point")
                                price = outcome.get("price")
                                
                                if not player_name:
                                    continue
                                
                                # Skip null lines unless it's an Anytime TD prop (which implies Yes/0.5)
                                if line is None and "anytime_td" not in market:
                                    continue
                                
                                # Find or create player
                                # Try to match by last name
                                last_name = player_name.split()[-1]
                                result = await session.execute(
                                    select(Player).where(
                                        Player.name.ilike(f"%{last_name}%")
                                    ).limit(1)
                                )
                                player = result.scalar_one_or_none()
                                
                                if not player:
                                    # Determine team and position
                                    
                                    # Try to find team using the roster map
                                    norm_name = player_name.lower().replace('.', '').replace("'", "")
                                    # Try direct match or fuzzy match
                                    found_team_id = player_team_map.get(norm_name)
                                    
                                    # Fallback: Check if last name is unique in the map
                                    if not found_team_id:
                                        last_name_search = player_name.split()[-1].lower()
                                        candidates = [tid for n, tid in player_team_map.items() if last_name_search in n]
                                        if len(set(candidates)) == 1: # Unique match
                                            found_team_id = candidates[0]
                                    
                                    # Final Fallback: Default to Home Team (but log warning)
                                    if not found_team_id:
                                        logger.warning(f"Could not map player {player_name} to a team. Defaulting to Home ({home_team.name})")
                                        team_id = home_team.id
                                    else:
                                        team_id = found_team_id

                                    position = "QB" if "pass" in market else "RB" if "rush" in market else "WR"
                                    
                                    player = Player(
                                        name=player_name,
                                        team_id=team_id,
                                        position=position,
                                        jersey_number="0"
                                    )
                                    session.add(player)
                                    await session.flush()
                                
                                # Check if prop exists
                                stat_type = STAT_MAP.get(market, market)
                                result = await session.execute(
                                    select(PlayerMarginal).where(
                                        (PlayerMarginal.game_id == game.id) &
                                        (PlayerMarginal.player_id == player.id) &
                                        (PlayerMarginal.stat_type == stat_type)
                                    )
                                )
                                existing = result.scalar_one_or_none()
                                
                                if existing:
                                    # Update odds
                                    if over_under == "Over":
                                        existing.over_odds = price
                                    else:
                                        existing.under_odds = price
                                    continue
                                
                                # Create new prop (only on first encounter)
                                if over_under == "Over":
                                    if "anytime" in stat_type or line is None:
                                        mean = 0.5
                                        std_dev = 1.0
                                        effective_line = 0.5
                                        z_score = 0 # Dummy
                                    else:
                                        mean = line + 10
                                        std_dev = 30 if "yds" in market else 1.5
                                        effective_line = line
                                        z_score = (line - mean) / std_dev
                                    
                                    under_prob = norm.cdf(z_score)
                                    over_prob = 1 - under_prob
                                    
                                    prop = PlayerMarginal(
                                        game_id=game.id,
                                        player_id=player.id,
                                        stat_type=stat_type,
                                        line=effective_line,
                                        mean=mean,
                                        std_dev=std_dev,
                                        over_probability=over_prob,
                                        under_probability=under_prob,
                                        over_odds=price,
                                        under_odds=-110.0 if "anytime" not in stat_type else None  # TD props don't usually have under
                                    )
                                    session.add(prop)
                                    props_for_game += 1
                                    total_props += 1
                
                await session.commit()
                logger.info(f"     ✅ Added {props_for_game} player props from FanDuel\n")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 INGESTION COMPLETE!")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Games Created: {total_games}")
        logger.info(f"✅ Player Props Created: {total_props}")
        logger.info(f"📊 Data Source: The Odds API (FanDuel)")
        logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(ingest_complete_data())
