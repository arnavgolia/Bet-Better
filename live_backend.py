#!/usr/bin/env python3
"""
Simplified Real Backend for SmartParlay
Fetches live sports data from The Odds API
Runs without Docker or Postgres
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import requests
from typing import List, Dict, Any

# The Odds API Configuration
ODDS_API_KEY = "9f112142a5f6e462f209ebd9b6d4b2af"  # From your .env file
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Sports to fetch
SPORTS = [
    "americanfootball_nfl",
    "basketball_nba", 
    "icehockey_nhl",
    "baseball_mlb",
    "soccer_epl",
    "soccer_uefa_champs_league"
]

def fetch_live_games() -> List[Dict[str, Any]]:
    """Fetch live games from The Odds API"""
    all_games = []
    
    for sport in SPORTS:
        try:
            url = f"{ODDS_API_BASE}/sports/{sport}/odds"
            params = {
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american",
                "dateFormat": "iso"
            }
            
            print(f"📡 Fetching {sport}...")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Transform to our format
            for game in data:
                transformed_game = {
                    "id": game.get("id"),
                    "sport": sport.upper().replace("_", " "),
                    "home_team": {
                        "id": game.get("home_team", "unknown"),
                        "name": game.get("home_team", "Unknown"),
                        "abbreviation": game.get("home_team", "UNK")[:3].upper()
                    },
                    "away_team": {
                        "id": game.get("away_team", "unknown"),
                        "name": game.get("away_team", "Unknown"),
                        "abbreviation": game.get("away_team", "UNK")[:3].upper()
                    },
                    "venue": None,
                    "commence_time": game.get("commence_time"),
                    "status": "scheduled",
                    "spread": None,
                    "total": None,
                    "temperature_f": None,
                    "wind_mph": None,
                    "precipitation_prob": None,
                    "created_at": datetime.now().isoformat()
                }
                
                # Extract spread and total from bookmakers
                if game.get("bookmakers"):
                    for bookmaker in game["bookmakers"]:
                        for market in bookmaker.get("markets", []):
                            if market["key"] == "spreads" and not transformed_game["spread"]:
                                # Get home team spread
                                for outcome in market.get("outcomes", []):
                                    if outcome["name"] == game["home_team"]:
                                        transformed_game["spread"] = outcome.get("point")
                                        break
                            elif market["key"] == "totals" and not transformed_game["total"]:
                                for outcome in market.get("outcomes", []):
                                    transformed_game["total"] = outcome.get("point")
                                    break
                
                all_games.append(transformed_game)
            
            print(f"✅ Found {len(data)} {sport} games")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"❌ API Key invalid for {sport}")
            elif e.response.status_code == 429:
                print(f"⚠️  Rate limit reached for {sport}")
            else:
                print(f"❌ HTTP Error {e.response.status_code} for {sport}")
        except Exception as e:
            print(f"❌ Error fetching {sport}: {str(e)}")
    
    print(f"\n📊 Total games fetched: {len(all_games)}\n")
    return all_games

class RealBackendHandler(BaseHTTPRequestHandler):
    # Cache games for 5 minutes
    _games_cache = None
    _cache_time = None
    _CACHE_DURATION = 300  # 5 minutes
    
    def _get_games(self) -> List[Dict[str, Any]]:
        """Get games with caching"""
        now = datetime.now().timestamp()
        
        if (self._games_cache is None or 
            self._cache_time is None or 
            now - self._cache_time > self._CACHE_DURATION):
            
            print("🔄 Refreshing games cache...")
            RealBackendHandler._games_cache = fetch_live_games()
            RealBackendHandler._cache_time = now
        
        return self._games_cache or []
    
    def do_GET(self):
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if self.path == '/health':
            response = {
                "status": "healthy", 
                "version": "live-v1", 
                "environment": "development",
                "data_source": "The Odds API (Live)"
            }
        elif self.path.startswith('/api/v1/games/') and '/marginals' not in self.path:
            # Get specific game by ID
            game_id = self.path.split('/')[4]
            games = self._get_games()
            game = next((g for g in games if g['id'] == game_id), None)
            if game:
                response = game
            else:
                response = {"detail": "Game not found"}
        elif self.path.startswith('/api/v1/players/game/') and '/marginals' in self.path:
            # Get player marginals for a game
            # For now, return empty array since we don't have player data
            response = []
        elif self.path.startswith('/api/v1/games'):
            response = self._get_games()
        else:
            response = {"detail": "Not Found"}
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if self.path == '/api/v1/parlays/generate':
            # For now, return a simple response
            # The full parlay logic requires JAX and complex simulation
            response = {
                "message": "Parlay generation requires full backend with JAX simulation",
                "status": "not_implemented"
            }
        else:
            response = {"detail": "Not Found"}
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    PORT = 8000
    server = HTTPServer(('localhost', PORT), RealBackendHandler)
    
    print("=" * 60)
    print("🚀 SmartParlay LIVE Backend Server")
    print("=" * 60)
    print(f"📍 Running at: http://localhost:{PORT}")
    print(f"📊 Health check: http://localhost:{PORT}/health")
    print(f"🎮 Games API: http://localhost:{PORT}/api/v1/games")
    print(f"🔑 Using The Odds API for live sports data")
    print(f"🏈 Sports: NFL, NBA, NHL, MLB, Soccer (EPL, Champions League)")
    print(f"\n⏱️  Games cache refreshes every 5 minutes")
    print(f"\nPress Ctrl+C to stop\n")
    print("=" * 60)
    
    # Fetch initial games
    print("\n🔄 Fetching initial games...\n")
    RealBackendHandler._games_cache = fetch_live_games()
    RealBackendHandler._cache_time = datetime.now().timestamp()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down backend...")
        server.shutdown()
