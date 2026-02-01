"""
Odds API Client Abstraction.
Supports multiple providers and a mock mode for development.
"""

from typing import List, Dict, Optional, Protocol, Any
from datetime import datetime, timedelta
import httpx
from app.core.config import settings
import logging
import random
from uuid import uuid4

logger = logging.getLogger(__name__)


class OddsClient(Protocol):
    """Protocol for fetching betting odds."""
    
    async def get_sports(self) -> List[Dict[str, Any]]:
        """Fetch active sports."""
        ...

    async def get_odds(
        self,
        sport: str,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american"
    ) -> List[Dict[str, Any]]:
        """Fetch odds for specific sport."""
        ...


class TheOddsApiClient:
    """Real client for The Odds API (the-odds-api.com)."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = settings.odds_api_base_url
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def get_sports(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/sports"
        params = {"apiKey": self.api_key}
        resp = await self.http_client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_odds(
        self,
        sport: str,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american"
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
            "dateFormat": "iso"
        }
        resp = await self.http_client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
        
    async def close(self):
        await self.http_client.aclose()


class MockOddsClient:
    """
    Simulates The Odds API responses for development.
    Generates realistic looking data for NFL/NBA without costing API credits.
    """
    
    async def get_sports(self) -> List[Dict[str, Any]]:
        return [
            {"key": "americanfootball_nfl", "active": True, "details": "NFL"},
            {"key": "basketball_nba", "active": True, "details": "NBA"}
        ]

    async def get_odds(
        self,
        sport: str,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american"
    ) -> List[Dict[str, Any]]:
        """Generate fake games with odds."""
        logger.info(f"Generating MOCK odds for {sport}")
        
        # Consistent mock data based on sport
        now = datetime.utcnow()
        games = []
        
        if "nfl" in sport:
            teams = [
                ("Kansas City Chiefs", "KC"), ("Buffalo Bills", "BUF"),
                ("Philadelphia Eagles", "PHI"), ("Dallas Cowboys", "DAL"),
                ("San Francisco 49ers", "SF"), ("Detroit Lions", "DET")
            ]
            league = "NFL"
        else:
            teams = [
                ("Los Angeles Lakers", "LAL"), ("Boston Celtics", "BOS"),
                ("Golden State Warriors", "GSW"), ("Denver Nuggets", "DEN")
            ]
            league = "NBA"

        for i in range(0, len(teams), 2):
            home_name, home_abbr = teams[i]
            away_name, away_abbr = teams[i+1]
            
            game_id = f"mock_{league.lower()}_{home_abbr}_{away_abbr}"
            commence_time = now + timedelta(days=i+1, hours=2)
            
            # Randomize lines slightly to simulate movement
            spread = -3.5 + random.choice([-0.5, 0, 0.5])
            total = 48.0 + random.choice([-1, 0, 1])
            
            game = {
                "id": game_id,
                "sport_key": sport,
                "commence_time": commence_time.isoformat() + "Z",
                "home_team": home_name,
                "away_team": away_name,
                "bookmakers": [
                    {
                        "key": "draftkings",
                        "title": "DraftKings",
                        "markets": [
                            {
                                "key": "spreads",
                                "outcomes": [
                                    {"name": home_name, "price": -110, "point": spread},
                                    {"name": away_name, "price": -110, "point": -spread}
                                ]
                            },
                            {
                                "key": "totals",
                                "outcomes": [
                                    {"name": "Over", "price": -110, "point": total},
                                    {"name": "Under", "price": -110, "point": total}
                                ]
                            },
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": home_name, "price": -175},
                                    {"name": away_name, "price": 145}
                                ]
                            }
                        ]
                    }
                ]
            }
            games.append(game)
            
        return games
        
    async def close(self):
        pass


def get_odds_client() -> Any:
    """Factory to get the appropriate client."""
    if settings.odds_api_key and settings.odds_api_key != "mock":
        return TheOddsApiClient(settings.odds_api_key)
    return MockOddsClient()
