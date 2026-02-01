# SmartParlay: AI-Powered SGP Optimizer

SmartParlay is an advanced sports betting analytics platform that uses **Student-t Copulas** and **JAX-accelerated simulations** to identify Expected Value (EV) in Same-Game Parlays. Unlike traditional tools that treat bets independently, SmartParlay models the **correlation** between player outcomes to find edges where sportsbooks undervalue the probability of linked events.

![Status](https://img.shields.io/badge/Status-Backend_Complete-success)
![Tech](https://img.shields.io/badge/Tech-FastAPI_JAX_Postgres-blue)

## 🚀 Key Features

*   **Correlation Engine**: Models the dependency between players (e.g., QB Passing Yards ↔ WR Receiving Yards).
*   **Regime Detection**: Automatically detects game scripts (Blowout, Shootout, Defensive Battle) and adjusts simulation parameters accordingly.
*   **Tail Dependency Modeling**: Uses Student-t Copulas to accurately model extreme events (where standard Gaussian models fail).
*   **Live Odds Ingestion**: Fetches real-time spreads and totals via The Odds API.
*   **High-Speed Simulation**: Runs 10,000 Monte Carlo simulations in <100ms using JAX.

## 🛠️ Architecture

*   **Backend**: Python, FastAPI, Pydantic V2
*   **Simulation**: JAX, NumPy, SciPy
*   **Database**: PostgreSQL 15, SQLAlchemy (Async), Alembic
*   **Infrastructure**: Docker Compose

## ⚡ Quick Start

### Prerequisites
*   Docker & Docker Compose
*   (Optional) API Key for [The Odds API](https://the-odds-api.com)

### 1. Start Services
```bash
docker-compose up -d --build
```
The API will be available at `http://localhost:8000`.
Docs: `http://localhost:8000/docs`.

### 2. Seed Data
SmartParlay needs base data (Teams, Players, Correlations) to function.
```bash
docker-compose exec backend python -m scripts.seed_nfl  # Seeds all 32 NFL Teams
docker-compose exec backend python -m scripts.seed_db   # Seeds sample Players & Correlations
```

### 3. Ingest Odds (Optional)
To fetch live game lines:
```bash
docker-compose exec backend python -m scripts.test_odds
```
*Note: Without an API key, this will use a Mock Client.*

### 4. Create a Parlay (Test)
You can generate a parlay recommendation via cURL:

```bash
curl -X POST "http://localhost:8000/api/v1/parlays/generate" \
-H "Content-Type: application/json" \
-d '{
  "game_id": "REPLACE_WITH_UUID_FROM_GAMES_ENDPOINT",
  "legs": [
    {
      "type": "player_prop",
      "player_id": "REPLACE_WITH_STAFFORD_ID",
      "stat": "pass_yards",
      "line": 265.5,
      "direction": "over",
      "odds": -110
    }
  ],
  "sportsbook": "draftkings"
}'
```

## 🏗️ Development Status

| Component | Status | Description |
|-----------|--------|-------------|
| **Database** | ✅ Done | Schema, Migrations, Seeding Scripts implemented |
| **API** | ✅ Done | Teams, Players, Games, Parlay Generation Endpoints |
| **Simulation** | ✅ Done | JAX Kernel, Correlation Matrix, Z-Score Norm |
| **Ingestion** | ✅ Done | Background worker for Game Lines |
| **Frontend** | ⏳ Pending | Next.js UI implementation needed |
| **Auth** | ⏳ Pending | User authentication system |

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes/       # Endpoints (parlay.py, games.py...)
│   │   ├── models/           # SQLAlchemy & Pydantic models
│   │   ├── services/
│   │   │   ├── copula/       # Math Engine (simulation.py, regime.py)
│   │   │   ├── odds/         # Data Ingestion (client.py, ingest.py)
│   │   │   └── parlay_service.py # Core Orchestrator
│   ├── scripts/              # Worker & Seed scripts
├── docker-compose.yml
└── HANDOFF.md                # Detailed technical handover report
```

---
**Next Steps:** Initialize the Frontend application to visualize these powerful insights.
