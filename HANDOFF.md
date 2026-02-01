# SmartParlay Project Status & Handoff Report

**Date:** February 1, 2026
**Version:** 0.5.0 (Backend Core Complete)

## 1. Project Overview
SmartParlay is an automated Same-Game Parlay (SGP) optimizer that identifies +EV (Expected Value) betting opportunities by modeling the correlation between player performances. unlike standard "+EV tools" that look at independent lines, SmartParlay simulates the game 10,000 times using a **Student-t Copula** to capture tail dependencies (e.g., "If Stafford throws for 300+ yards, chances are Kupp also went over").

## 2. Architecture Status
The system is built on a modern Python Async stack.

*   **Backend:** FastAPI (Async), Pydantic V2.
*   **Database:** PostgreSQL 15 with SQLAlchemy (AsyncPG).
*   **Simulation Engine:** JAX (Google's accelerated linear algebra library) for high-speed Monte Carlo simulations (currently achieving <700ms latency for 10k sims).
*   **Infrastructure:** Docker Compose (Backend, Postgres).

## 3. What Has Been Built (Completed)

### A. Core Database Schema (`backend/app/models/database/`)
*   **Teams/Games/Venues:** Standard relational models.
*   **PlayerMarginals:** Stores projected stats (Mean, StdDev) and Lines for players.
*   **PlayerCorrelations:** Stores pairwise correlation coefficients (e.g., Stafford-Kupp = 0.75).
*   **ParlayRecommendations:** Stores generated bets and their EV metrics.

### B. The Simulation Engine (The "Brain")
*   **JAX Kernel (`backend/app/services/copula/simulation.py`):** A custom JIT-compiled simulation engine that uses Cholesky decomposition to generate correlated random variables.
*   **Regime Detection (`backend/app/services/copula/regime.py`):** Logic to detect "Script" (Blowout vs Shootout) and dynamic adjustment of the "Nu" parameter (degrees of freedom).
*   **Parlay Service (`backend/app/services/parlay_service.py`):**
    *   **Z-Score Normalization:** implemented robust inputs normalization: `(Line - Mean) / StdDev` to feed the standardized Student-t kernel.
    *   **Direction Logic:** Implemented advanced handling for "Under" bets by flipping correlation signs (conceptually simulating `-Z`).

### C. API Endpoints
*   `GET /api/v1/teams`: List all teams.
*   `GET /api/v1/games`: List upcoming games with live Odds.
*   `POST /api/v1/parlays/generate`: The core endpoint. Takes a proposed parlay, runs the simulation, and returns True/Implied Probability and EV%.

### D. Odds Ingestion
*   **Client:** `TheOddsApiClient` implemented with a fallback `MockOddsClient`.
*   **Worker:** `backend/scripts/odds_worker.py` runs in the background to fetch "Upcoming NFL Games" and update Spreads/Totals in the DB.
*   **Data:** Seeded all 32 NFL Teams to ensure ingestion mapping works.

## 4. How to Run / Verify (Instructions for Next Agent)

1.  **Start Services:**
    ```bash
    docker-compose up -d --build
    ```

2.  **Seed Data (Teams, Players, Correlations):**
    ```bash
    docker-compose exec backend python -m scripts.seed_db
    docker-compose exec backend python -m scripts.seed_nfl
    ```

3.  **Run Odds Ingestion:**
    ```bash
    # Run a single cycle to fetch live lines
    docker-compose exec backend python -m scripts.test_odds
    # OR run the continuous worker
    docker-compose exec backend python -m scripts.odds_worker
    ```

4.  **Test The Core Engine:**
    ```bash
    # Generate a Parlay (Check .agent/workflows/test_parlay.md for Curl)
    curl -X POST "http://localhost:8000/api/v1/parlays/generate" ...
    ```

## 5. Remaining Work / Next Steps

### Immediate Priority: Frontend Implementation
The backend is ready. The next major step is building the **Next.js** frontend.
*   **Tasks:**
    *   Initialize Next.js + Tailwind + Shadcn/UI.
    *   Create "Game List" page fetching `GET /games`.
    *   Create "Parlay Builder" page where users select a game, add player props, and click "Analyze".

### Secondary Priority: Enhanced Data Engineering
Currently, **Player Prop Lines** (e.g., "Stafford Over 265.5") are **Seeded** (Static). 
*   **Task:** We ingest Game Lines (Spread/Total), but we need to ingest *Player Props*. The Odds API has a `player_props` market (requires higher tier key or specific endpoint configuration).
*   **Action:** Update `ingest.py` to fetch `player_pass_yds`, `player_reception_yds` and upsert into `PlayerMarginal`.

### Technical Debt / Notes
1.  **Authorization:** API is currently open. Need to implement JWT Auth if this goes public.
2.  **Correlation Generation:** Correlations are currently seeded/static. Future work involves writing a script to calculate these from historical play-by-play data (e.g., using `nfl_data_py`).
3.  **Pydantic Validator:** In `app/models/schemas/parlay.py`, the `check_recommendation_logic` validator is commented out due to V2 context issues. Logic is enforced in Service layer, but should be fixed eventually.

## 6. Critical Files
*   `backend/app/services/parlay_service.py`: Orchestrator.
*   `backend/app/services/copula/simulation.py`: Math Kernel.
*   `backend/app/services/odds/ingest.py`: Data Pipeline.
*   `backend/scripts/`: Operations scripts.
