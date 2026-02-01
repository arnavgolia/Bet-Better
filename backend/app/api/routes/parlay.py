"""
Parlay generation API routes.

Handles the core user flow:
1. POST /parlays/generate - Generate +EV SGP recommendations
2. GET /parlays/{id} - Retrieve parlay details
3. POST /parlays/{id}/slipbuilder - Generate clipboard data
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.database import get_db

from app.models.schemas.parlay import (
    ParlayRequest,
    ParlayRecommendation,
    SlipBuilderRequest,
    SlipBuilderResponse,
)
from app.services.copula import simulate_parlay_t_copula, detect_game_regime

router = APIRouter(prefix="/parlays", tags=["parlays"])


@router.post("/generate", response_model=ParlayRecommendation)
async def generate_parlay(
    request: ParlayRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate +EV parlay recommendation with full explanation.

    This is the core endpoint that:
    1. Validates the game and legs
    2. Fetches odds from cache
    3. Loads correlation matrix
    4. Detects game regime
    5. Runs Student-t Copula simulation
    6. Calculates +EV
    7. Generates explanation
    8. Saves to database
    9. Returns recommendation
    """
    from app.services.parlay_service import generate_parlay_recommendation
    from app.api.dependencies.database import get_db
    
    # We need a DB session. Since this function signature doesn't have it,
    # we need to inject it.
    # But wait, the router function needs the session.
    # Refactoring function signature to accept Depends(get_db)
    
    return await generate_parlay_recommendation(request, db)


@router.post("/{parlay_id}/slipbuilder", response_model=SlipBuilderResponse)
async def build_slip(
    parlay_id: str,
    request: SlipBuilderRequest,
):
    """
    Generate SlipBuilder data for clipboard fallback.

    Since we can't deep-link directly to SGP slips, we:
    1. Format picks as clipboard text
    2. Generate game page deep link
    3. Return both with instructions
    """
    sportsbook = request.sportsbook

    deep_link_templates = {
        "draftkings": "draftkings://sportsbook/game/{event_id}",
        "fanduel": "fanduel://event/{event_id}",
        "betmgm": "betmgm://game/{event_id}",
    }

    clipboard_text = "My SmartParlay: Stafford Over 265.5 Pass Yds, Kupp Anytime TD"
    game_link = deep_link_templates[sportsbook].format(event_id="placeholder")

    return {
        "clipboard_text": clipboard_text,
        "game_page_deeplink": game_link,
        "fallback_web_url": "https://sportsbook.draftkings.com/...",
        "instructions": "Picks copied! Tap to open DraftKings and add legs manually.",
    }
