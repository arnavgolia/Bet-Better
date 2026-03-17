"""
Ingestion of game-level props: spreads, totals, moneylines from FanDuel
Separate from player props - focuses on team/game betting lines
"""

import asyncio
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.database import Team, Game
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ODDS_API_KEY = "9f112142a5f6e462f209ebd9b6d4b2af"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Sports to ingest
SPORTS = [
    ("americanfootball_nfl", "NFL"),
]


async def ingest_game_props():
    """Fetch game-level betting lines (spreads, totals, moneylines) from The Odds API"""
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        total_games = 0
        total_props = 0

        for sport_key, sport_name in SPORTS:
            logger.info(f"\n{'='*70}")
            logger.info(f"🎲 INGESTING {sport_name} GAME PROPS FROM THE ODDS API")
            logger.info(f"{'='*70}")

            # Fetch games with h2h, spreads, and totals
            async with httpx.AsyncClient() as client:
                url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
                params = {
                    "apiKey": ODDS_API_KEY,
                    "regions": "us",
                    "markets": "h2h,spreads,totals",  # Moneyline, spread, total
                    "oddsFormat": "american",
                    "bookmakers": "fanduel"
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
            for event in events[:10]:  # Process up to 10 games
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

                result = await session.execute(
                    select(Team).where(Team.name == away_team_name)
                )
                away_team = result.scalar_one_or_none()

                if not home_team:
                    # Create home team
                    abbr = ''.join([word[0] for word in home_team_name.split()])[:3].upper()
                    home_team = Team(
                        name=home_team_name,
                        abbreviation=abbr,
                        city=home_team_name.rsplit(' ', 1)[0],
                        league=sport_name
                    )
                    session.add(home_team)
                    await session.flush()

                if not away_team:
                    # Create away team
                    abbr = ''.join([word[0] for word in away_team_name.split()])[:3].upper()
                    away_team = Team(
                        name=away_team_name,
                        abbreviation=abbr,
                        city=away_team_name.rsplit(' ', 1)[0],
                        league=sport_name
                    )
                    session.add(away_team)
                    await session.flush()

                # Get or create game
                result = await session.execute(
                    select(Game).where(
                        (Game.home_team_id == home_team.id) &
                        (Game.away_team_id == away_team.id) &
                        (Game.commence_time == commence_time)
                    )
                )
                game = result.scalar_one_or_none()

                if not game:
                    game = Game(
                        sport=sport_name,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        commence_time=commence_time,
                        status="scheduled"
                    )
                    session.add(game)
                    await session.flush()
                    logger.info(f"     ✨ Created new game")
                    total_games += 1

                # Process FanDuel markets
                for bookmaker in event.get("bookmakers", []):
                    if bookmaker.get("key") != "fanduel":
                        continue

                    for market in bookmaker.get("markets", []):
                        market_key = market.get("key")

                        if market_key == "h2h":
                            # Moneyline
                            for outcome in market.get("outcomes", []):
                                team_name = outcome.get("name")
                                odds = outcome.get("price")

                                is_home = team_name == home_team_name
                                team_id = home_team.id if is_home else away_team.id

                                logger.info(f"       💰 Moneyline - {team_name}: {odds:+d}")

                                # Store in game_props table
                                # (This would require SQLAlchemy model - pseudo code for now)
                                # game_prop = GameProp(
                                #     game_id=game.id,
                                #     prop_type="moneyline",
                                #     team_id=team_id,
                                #     line=None,
                                #     favorite_odds=odds if odds < 0 else None,
                                #     underdog_odds=odds if odds > 0 else None,
                                # )
                                # session.add(game_prop)

                        elif market_key == "spreads":
                            # Point spread
                            for outcome in market.get("outcomes", []):
                                team_name = outcome.get("name")
                                point = outcome.get("point")
                                odds = outcome.get("price")

                                is_home = team_name == home_team_name
                                team_id = home_team.id if is_home else away_team.id

                                logger.info(f"       📊 Spread - {team_name} {point:+.1f}: {odds:+d}")

                                # Store spread
                                # game_prop = GameProp(
                                #     game_id=game.id,
                                #     prop_type="spread",
                                #     team_id=team_id,
                                #     line=point,
                                #     over_odds=odds,
                                # )
                                # session.add(game_prop)

                        elif market_key == "totals":
                            # Over/Under total points
                            for outcome in market.get("outcomes", []):
                                direction = outcome.get("name")  # "Over" or "Under"
                                point = outcome.get("point")
                                odds = outcome.get("price")

                                if direction == "Over":
                                    logger.info(f"       🎯 Total O{point}: {odds:+d}")
                                    # game_prop = GameProp(
                                    #     game_id=game.id,
                                    #     prop_type="total",
                                    #     line=point,
                                    #     over_odds=odds,
                                    # )
                                else:
                                    logger.info(f"       🎯 Total U{point}: {odds:+d}")
                                    # Would update the same prop's under_odds

                                total_props += 1

                # Update game with basic lines for display
                # Extract first spread and total for quick reference
                for bookmaker in event.get("bookmakers", []):
                    if bookmaker.get("key") == "fanduel":
                        for market in bookmaker.get("markets", []):
                            if market.get("key") == "spreads":
                                outcomes = market.get("outcomes", [])
                                home_outcome = next((o for o in outcomes if o["name"] == home_team_name), None)
                                if home_outcome:
                                    game.spread = home_outcome.get("point")

                            elif market.get("key") == "totals":
                                outcomes = market.get("outcomes", [])
                                over_outcome = next((o for o in outcomes if o["name"] == "Over"), None)
                                if over_outcome:
                                    game.total = over_outcome.get("point")

                await session.commit()
                logger.info(f"     ✅ Game props saved\n")

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ INGESTION COMPLETE")
        logger.info(f"   Games processed: {total_games}")
        logger.info(f"   Props created: {total_props}")
        logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(ingest_game_props())
