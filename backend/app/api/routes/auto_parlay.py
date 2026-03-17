"""
Auto-Parlay API Endpoints
Allows users to request auto-built parlays via natural language
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging
import time

from app.api.dependencies.database import get_db
from app.services.auto_parlay.intent_parser import IntentParser, UserIntent
from app.services.auto_parlay.candidate_generator import CandidateGenerator, ConstraintValidator
from app.services.auto_parlay.parlay_scorer import ParlayScorer, ParlayOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-parlay", tags=["auto-parlay"])


# ===== REQUEST/RESPONSE MODELS =====

class AutoParlayRequest(BaseModel):
    """Request to auto-build a parlay"""
    user_input: str = Field(..., description="Natural language parlay request", min_length=5)
    user_id: str | None = Field(None, description="Optional user ID for tracking")

    class Config:
        schema_extra = {
            "example": {
                "user_input": "Build me a 5-leg parlay for the Super Bowl",
                "user_id": "user_12345"
            }
        }


class PropLegResponse(BaseModel):
    """Individual leg in the parlay"""
    player_name: str | None
    stat_type: str
    line: float | None
    direction: str  # "over" or "under"
    odds: int
    confidence: float
    primary_reason: str
    supporting_factors: List[str]


class ParlayResponse(BaseModel):
    """Complete parlay with analysis"""
    parlay_id: str
    legs: List[PropLegResponse]
    num_legs: int
    overall_score: float
    expected_value: float
    win_probability: float
    parlay_odds: int
    correlation: float
    confidence: float
    risk_profile: str
    summary: str
    reasoning: str


class AlternativeParlay(BaseModel):
    """Alternative parlay version"""
    type: str  # "safer", "riskier", "same_game"
    description: str
    parlay: ParlayResponse


class AutoParlayResponse(BaseModel):
    """Full response with primary and alternatives"""
    primary_parlay: ParlayResponse
    alternatives: List[AlternativeParlay]
    intent: Dict[str, Any]
    build_time_ms: int
    candidates_considered: int


# ===== ENDPOINTS =====

@router.post("/build", response_model=AutoParlayResponse)
async def build_auto_parlay(
    request: AutoParlayRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-build a parlay from natural language request

    This is the main endpoint that:
    1. Parses user intent
    2. Generates candidate props
    3. Scores combinations
    4. Returns optimal parlay + alternatives
    """
    start_time = time.time()

    try:
        # Step 1: Parse user intent
        logger.info(f"Parsing intent: {request.user_input}")
        parser = IntentParser()
        intent = parser.parse(request.user_input)

        logger.info(f"Parsed intent: {intent.num_legs} legs, {intent.risk_profile}, {intent.sports}")

        # Step 2: Validate constraints
        validator = ConstraintValidator(db)
        validation = await validator.validate(intent)

        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'Invalid constraints',
                    'errors': validation['errors'],
                    'warnings': validation['warnings']
                }
            )

        # Step 3: Generate candidates
        logger.info(f"Generating candidates...")
        generator = CandidateGenerator(db)
        candidates = await generator.generate_candidates(intent)

        if len(candidates) < intent.num_legs:
            raise HTTPException(
                status_code=404,
                detail={
                    'error': 'Insufficient data',
                    'message': f'Only {len(candidates)} props available, need {intent.num_legs}',
                    'suggestion': 'Try reducing leg count or expanding filters'
                }
            )

        # Step 4: Build optimal parlay
        logger.info(f"Optimizing from {len(candidates)} candidates...")
        scorer = ParlayScorer()
        optimizer = ParlayOptimizer(scorer)

        result = await optimizer.build_optimal_parlay(candidates, intent)

        # Step 5: Format response
        primary_parlay = _format_parlay_response(
            result['primary'],
            intent
        )

        alternatives = []
        for alt in result.get('alternatives', []):
            alt_parlay = _format_parlay_response(alt['parlay'], intent)
            alternatives.append(AlternativeParlay(
                type=alt['type'],
                description=alt['description'],
                parlay=alt_parlay
            ))

        build_time = int((time.time() - start_time) * 1000)

        return AutoParlayResponse(
            primary_parlay=primary_parlay,
            alternatives=alternatives,
            intent=intent.dict(),
            build_time_ms=build_time,
            candidates_considered=len(candidates)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building parlay: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={'error': 'Internal server error', 'message': str(e)}
        )


@router.post("/parse-intent", response_model=Dict[str, Any])
async def parse_intent_only(request: AutoParlayRequest):
    """
    Parse intent without building parlay (for debugging/preview)
    """
    try:
        parser = IntentParser()
        intent = parser.parse(request.user_input)

        return {
            'intent': intent.dict(),
            'interpretation': _generate_intent_summary(intent)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/available-games")
async def get_available_games(
    sport: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of available games for parlay building
    """
    from app.models.database import Game
    from sqlalchemy import select, and_
    from datetime import datetime

    query = select(Game).where(
        and_(
            Game.status == 'scheduled',
            Game.commence_time > datetime.now()
        )
    )

    if sport:
        query = query.where(Game.sport == sport)

    result = await db.execute(query)
    games = result.scalars().all()

    return {
        'games': [
            {
                'id': str(game.id),
                'sport': game.sport,
                'home_team': game.home_team.name if game.home_team else None,
                'away_team': game.away_team.name if game.away_team else None,
                'commence_time': game.commence_time.isoformat(),
                'spread': game.spread,
                'total': game.total
            }
            for game in games
        ],
        'count': len(games)
    }


# ===== HELPER FUNCTIONS =====

def _format_parlay_response(scored_parlay, intent: UserIntent) -> ParlayResponse:
    """Convert ScoredParlay to ParlayResponse"""
    import uuid

    legs_response = []
    for leg in scored_parlay.legs:
        legs_response.append(PropLegResponse(
            player_name=leg.player.name if leg.player else None,
            stat_type=leg.stat_type,
            line=leg.line,
            direction=leg.recommended_direction,
            odds=leg.over_odds if leg.recommended_direction == 'over' else leg.under_odds,
            confidence=leg.model_confidence or 0.7,
            primary_reason=_generate_leg_reason(leg),
            supporting_factors=_generate_supporting_factors(leg)
        ))

    # Calculate parlay odds
    parlay_odds = _calculate_parlay_odds(scored_parlay.legs)

    return ParlayResponse(
        parlay_id=str(uuid.uuid4()),
        legs=legs_response,
        num_legs=len(scored_parlay.legs),
        overall_score=scored_parlay.score.overall,
        expected_value=scored_parlay.score.expected_value,
        win_probability=scored_parlay.score.win_probability,
        parlay_odds=parlay_odds,
        correlation=scored_parlay.score.correlation,
        confidence=scored_parlay.score.confidence,
        risk_profile=intent.risk_profile.value,
        summary=_generate_parlay_summary(scored_parlay, intent),
        reasoning=_generate_parlay_reasoning(scored_parlay, intent)
    )


def _calculate_parlay_odds(legs: List) -> int:
    """Calculate combined American odds"""
    total_decimal = 1.0

    for leg in legs:
        odds = leg.over_odds if leg.recommended_direction == 'over' else leg.under_odds
        if odds > 0:
            decimal = (odds / 100) + 1
        else:
            decimal = (100 / abs(odds)) + 1

        total_decimal *= decimal

    # Convert back to American
    if total_decimal >= 2:
        return int((total_decimal - 1) * 100)
    else:
        return int(-100 / (total_decimal - 1))


def _generate_leg_reason(leg) -> str:
    """Generate primary reason for selecting this leg"""
    player_name = leg.player.name if leg.player else "Team"
    stat_label = leg.stat_type.replace('_', ' ').title()

    return f"{player_name} has favorable matchup for {stat_label}"


def _generate_supporting_factors(leg) -> List[str]:
    """Generate supporting factors for leg selection"""
    factors = []

    if leg.sharp_percentage and leg.sharp_percentage > 60:
        factors.append(f"Sharp money backing this ({leg.sharp_percentage:.0f}%)")

    if leg.historical_hit_rate and leg.historical_hit_rate > 0.6:
        factors.append(f"Historical hit rate: {leg.historical_hit_rate*100:.0f}%")

    if leg.weather_impact and leg.weather_impact > 0.05:
        factors.append("Favorable weather conditions")

    if not factors:
        factors.append("Strong statistical projection")

    return factors


def _generate_parlay_summary(scored_parlay, intent: UserIntent) -> str:
    """Generate one-line summary"""
    profile_map = {
        'safe': 'conservative',
        'balanced': 'balanced',
        'aggressive': 'high-upside',
        'degen': 'moonshot'
    }

    profile_desc = profile_map.get(intent.risk_profile.value, 'balanced')

    return (
        f"{intent.num_legs}-leg {profile_desc} parlay with "
        f"{scored_parlay.score.win_probability*100:.1f}% win probability"
    )


def _generate_parlay_reasoning(scored_parlay, intent: UserIntent) -> str:
    """Generate detailed reasoning"""
    reasoning = (
        f"I've built a {intent.num_legs}-leg parlay optimized for your {intent.risk_profile.value} "
        f"risk profile. Your estimated win probability is {scored_parlay.score.win_probability*100:.1f}%, "
        f"with an expected value of ${scored_parlay.score.expected_value:.2f} per $100 bet."
    )

    # Add correlation note
    corr = scored_parlay.score.correlation
    if abs(corr) < 0.2:
        reasoning += " The legs are mostly independent, providing good variance."
    elif corr > 0.4:
        reasoning += " The legs are positively correlated, moving together for safer outcomes."

    return reasoning


def _generate_intent_summary(intent: UserIntent) -> str:
    """Generate human-readable summary of parsed intent"""
    return (
        f"I understand you want: {intent.num_legs} legs, {intent.risk_profile.value} risk, "
        f"sports: {', '.join(intent.sports)}, "
        f"props: {', '.join([c.value for c in intent.allowed_prop_types])}"
    )
