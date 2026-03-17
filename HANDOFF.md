# SmartParlay Project Status & Handoff Report

**Date:** February 1, 2026
**Version:** 0.6.0 (Full Stack Integrated & Debugged)

## 1. Project Overview
SmartParlay is an automated Same-Game Parlay (SGP) optimizer that identifies +EV (Expected Value) betting opportunities by modeling the correlation between player performances. The system uses a **Student-t Copula** simulation engine (JAX-accelerated) to capture tail dependencies (e.g., "If QBs throw deep, WRs likely go over").

## 2. Architecture Status
The system is now a fully integrated Full Stack application.

*   **Frontend:** Next.js 14, Tailwind CSS, Lucide React (UI Components), React Query (State Management).
*   **Backend:** FastAPI (Async), Pydantic V2, PostgreSQL 15, Redis.
*   **Simulation Engine:** JAX Monte Carlo kernel running correlations.
*   **Data Pipeline:** "The Odds API" integration for Game Lines, Player Props, and metadata.

## 3. Recent Major Achievements (Session Goals)

### A. Frontend Implementation & UI Refinement
*   **Parlay Builder Page (`/parlay/[gameId]`):**
    *   Rebuilt UI to mimic FanDuel/DraftKings aesthetics (Dark mode, Tabs for Passing/Rushing/Received/TDs).
    *   Implemented **Interactive Betslip**: Users can toggle legs, see odds, and submit for analysis.
    *   **Analysis Results**: Displays "Recommended" status, EV%, True Probability, and detailed insights.
    *   **Validation**: Added client-side checks (e.g., minimum 2 legs required) to prevent premature API calls.

### B. Critical Data Ingestion Fixes
*   **Team Mapping Fix:** Solved a critical bug where players were defaulting to the Home Team. Implemented **ESPN Roster Lookup** to correctly map players (e.g., Kenneth Walker -> Seahawks) regardless of API inconsistencies.
*   **TD Scorer Ingestion:** Fixed a bug where "Anytime TD" props were skipped because they lacked a "line" (points) value. Logic now correctly handles "Yes" outcomes and implicit 0.5 lines.
*   **Rate Limit Handling:** Resolved missing "Receiving Yards" props by optimizing ingestion runs (and retrying successful markets).

### C. Backend Stability
*   **Analysis API Fix (422 Error):** Resolved a schema mismatch between the Database (`passing_yards`) and Pydantic Models (`pass_yards`). Updated `PropType` Enum to strictly match the database sources.
*   **JAX Config:** Configured JAX to run efficiently on CPU (avoiding TPU/ROCm warnings in Docker).

## 4. Current Workflow (How it Works)

1.  **Ingest Data:**
    *   Script: `backend/scripts/ingest_fanduel_data.py`
    *   Fetches Odds/Props -> Maps Players (ESPN) -> Calculates implied probs -> Stores in Postgres.
2.  **View Games (Frontend):**
    *   Home Page lists active games.
3.  **Build Parlay:**
    *   User selects Game -> Selects Props (Over/Under).
4.  **Analyze:**
    *   Frontend sends payload to `POST /api/v1/parlays/generate`.
    *   Backend retrieves correlations -> Runs 10,000 simulations -> Returns EV.

## 5. Known Issues / Constraints
*   **API Data Sparsity:** "Anytime TD" props rely on "The Odds API" coverage, which can be spotty for some games. We have successfully ingested records, but coverage varies.
*   **Rate Limits:** The free tier of The Odds API is strict (requests per second). Data ingestion should be run carefully to avoid 429 errors.

## 6. Next Steps (Roadmap)
1.  **Historical Correlations:** Currently, correlations are seeded or estimated. We need to implement a pipeline (e.g., `nfl_data_py`) to calculate *real* historical correlations between specific QB/WR pairs.
2.  **Authentication:** Implement User Auth (JWT/NextAuth) for saving betting history.
3.  **Bankroll Management:** Enhance the "Kelly Criterion" suggestion in the Analysis result.

## 7. Critical Files
*   **Frontend**: `frontend/app/parlay/[gameId]/page.tsx` (Main UI Logic)
*   **Ingestion**: `backend/scripts/ingest_fanduel_data.py` (Data Pipeline & Logic)
*   **Schema**: `backend/app/models/schemas/parlay.py` (API Contract)
*   **Service**: `backend/app/services/parlay_service.py` (Core Logic)
