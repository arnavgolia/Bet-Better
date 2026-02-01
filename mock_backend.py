#!/usr/bin/env python3
"""
Lightweight mock backend for SmartParlay
Runs without Docker, Postgres, or any dependencies
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
import uuid

# Mock data
MOCK_GAMES = [
    {
        "id": str(uuid.uuid4()),
        "sport": "NFL",
        "home_team": {
            "id": str(uuid.uuid4()),
            "name": "Los Angeles Rams",
            "abbreviation": "LAR"
        },
        "away_team": {
            "id": str(uuid.uuid4()),
            "name": "Seattle Seahawks",
            "abbreviation": "SEA"
        },
        "venue": {
            "id": str(uuid.uuid4()),
            "name": "SoFi Stadium",
            "city": "Inglewood",
            "is_dome": True
        },
        "commence_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "status": "scheduled",
        "spread": -3.5,
        "total": 48.5,
        "temperature_f": 72,
        "wind_mph": 0,
        "precipitation_prob": 0.0,
        "created_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "sport": "NFL",
        "home_team": {
            "id": str(uuid.uuid4()),
            "name": "Kansas City Chiefs",
            "abbreviation": "KC"
        },
        "away_team": {
            "id": str(uuid.uuid4()),
            "name": "Buffalo Bills",
            "abbreviation": "BUF"
        },
        "venue": {
            "id": str(uuid.uuid4()),
            "name": "Arrowhead Stadium",
            "city": "Kansas City",
            "is_dome": False
        },
        "commence_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "status": "scheduled",
        "spread": -2.5,
        "total": 52.5,
        "temperature_f": 45,
        "wind_mph": 12,
        "precipitation_prob": 0.2,
        "created_at": datetime.now().isoformat()
    }
]

class MockBackendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if self.path == '/health':
            response = {"status": "healthy", "version": "mock-v1", "environment": "development"}
        elif self.path.startswith('/api/v1/games'):
            response = MOCK_GAMES
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
            # Mock parlay response
            response = {
                "id": str(uuid.uuid4()),
                "legs": [],
                "total_odds": -110,
                "expected_value": 0.05,
                "win_probability": 0.52,
                "recommendation": "STRONG_BET",
                "kelly_fraction": 0.02,
                "simulation_results": {
                    "mean_payout": 1.91,
                    "std_payout": 0.95,
                    "win_rate": 0.52
                },
                "created_at": datetime.now().isoformat()
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
    server = HTTPServer(('localhost', PORT), MockBackendHandler)
    print(f"🚀 Mock Backend Server running at http://localhost:{PORT}")
    print(f"📊 Health check: http://localhost:{PORT}/health")
    print(f"🎮 Games API: http://localhost:{PORT}/api/v1/games")
    print(f"\nPress Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down mock backend...")
        server.shutdown()
