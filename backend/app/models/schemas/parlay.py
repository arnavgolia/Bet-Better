"""
Pydantic schemas for parlay API requests and responses.

These models handle validation, serialization, and documentation.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


class BetType(str, Enum):
    """Types of bets supported in SGP legs."""
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE = "moneyline"
    PLAYER_PROP = "player_prop"


class PropType(str, Enum):
    """Player proposition bet types."""
    PASSING_YARDS = "passing_yards"
    RUSHING_YARDS = "rushing_yards"
    RECEIVING_YARDS = "receiving_yards"
    PASSING_TDS = "passing_tds"
    ANYTIME_TDS = "anytime_tds"
    RECEPTIONS = "receptions"
    PASS_ATTEMPTS = "pass_attempts"
    COMPLETIONS = "completions"
    INTERCEPTIONS = "interceptions"


class PropDirection(str, Enum):
    """Bet direction for prop bets."""
    OVER = "over"
    UNDER = "under"


class Sportsbook(str, Enum):
    """Supported sportsbooks."""
    DRAFTKINGS = "draftkings"
    FANDUEL = "fanduel"
    BETMGM = "betmgm"
    CAESARS = "caesars"
    POINTSBET = "pointsbet"


# Request Models

class ParlayLegRequest(BaseModel):
    """Individual leg of a parlay."""

    type: BetType
    team_id: Optional[str] = None
    player_id: Optional[str] = None
    stat: Optional[PropType] = None
    line: float
    direction: Optional[PropDirection] = None  # For props
    odds: int = Field(..., description="American odds (e.g., -110, +250)")

    @validator("player_id")
    def validate_player_prop(cls, v, values):
        """Ensure player_id is provided for player props."""
        if values.get("type") == BetType.PLAYER_PROP and not v:
            raise ValueError("player_id required for player_prop bets")
        return v

    class Config:
        schema_extra = {
            "example": {
                "type": "player_prop",
                "player_id": "stafford_01",
                "stat": "pass_yards",
                "line": 265.5,
                "direction": "over",
                "odds": -110,
            }
        }


class WeatherContext(BaseModel):
    """Weather conditions affecting the game."""

    wind_mph: Optional[int] = Field(None, ge=0, le=100)
    temp_f: Optional[int] = Field(None, ge=-20, le=120)
    precip_prob: Optional[float] = Field(None, ge=0, le=1)
    conditions: Optional[str] = None  # "clear", "rain", "snow", etc.

    class Config:
        schema_extra = {
            "example": {
                "wind_mph": 12,
                "temp_f": 55,
                "precip_prob": 0.1,
                "conditions": "partly_cloudy",
            }
        }


class InjuryContext(BaseModel):
    """Player injury information."""

    player_id: str
    player_name: str
    status: str = Field(..., description="out, doubtful, questionable, probable")
    impact: float = Field(..., ge=0, le=1, description="Estimated impact on performance (0-1)")
    position: str


class ParlayRequest(BaseModel):
    """Request to generate a parlay recommendation."""

    game_id: str = Field(..., description="Unique game identifier")
    legs: List[ParlayLegRequest] = Field(..., min_items=2, max_items=6)
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context: weather, injuries, sentiment, etc."
    )
    sportsbook: Optional[Sportsbook] = Field(
        default=Sportsbook.DRAFTKINGS,
        description="Target sportsbook for odds"
    )

    @validator("legs")
    def validate_legs_count(cls, v):
        """Ensure reasonable number of legs."""
        if len(v) < 2:
            raise ValueError("Parlay must have at least 2 legs")
        if len(v) > 6:
            raise ValueError("Parlay cannot have more than 6 legs (accuracy degrades)")
        return v

    class Config:
        schema_extra = {
            "example": {
                "game_id": "nfl_2026_01_05_sea_lar",
                "legs": [
                    {
                        "type": "spread",
                        "team_id": "sea",
                        "line": 3.5,
                        "odds": -110,
                    },
                    {
                        "type": "player_prop",
                        "player_id": "stafford_01",
                        "stat": "pass_yards",
                        "line": 265.5,
                        "direction": "over",
                        "odds": -110,
                    },
                ],
                "context": {
                    "weather": {"wind_mph": 12, "temp_f": 55},
                    "injuries": []
                },
                "sportsbook": "draftkings",
            }
        }


class SlipBuilderRequest(BaseModel):
    """Request to generate SlipBuilder data."""

    sportsbook: Sportsbook

    class Config:
        schema_extra = {
            "example": {
                "sportsbook": "draftkings"
            }
        }


# Response Models

class ExplanationFactor(BaseModel):
    """Individual factor explaining the prediction."""

    name: str
    impact: float = Field(..., ge=-1, le=1, description="Impact on probability (-1 to 1)")
    direction: str = Field(..., description="positive, negative, or neutral")
    detail: str
    confidence: float = Field(..., ge=0, le=1)

    class Config:
        schema_extra = {
            "example": {
                "name": "Weather: High Wind",
                "impact": -0.15,
                "direction": "negative",
                "detail": "12 mph wind reduces passing efficiency by ~15%",
                "confidence": 0.90,
            }
        }


class ParlayExplanation(BaseModel):
    """Explainable AI breakdown of the prediction."""

    overall_confidence: float = Field(..., ge=0, le=1)
    factors: List[ExplanationFactor]
    regime_detected: str
    regime_reasoning: str

    class Config:
        schema_extra = {
            "example": {
                "overall_confidence": 0.78,
                "factors": [
                    {
                        "name": "Opponent Pass Defense",
                        "impact": -0.15,
                        "direction": "negative",
                        "detail": "SEA ranked #1 in pass defense DVOA",
                        "confidence": 0.85,
                    }
                ],
                "regime_detected": "normal",
                "regime_reasoning": "Standard conditions (spread +3.5, total 48)",
            }
        }


class ParlayRecommendation(BaseModel):
    """Complete parlay recommendation with analysis."""

    parlay_id: str
    game_id: str
    recommended: bool = Field(..., description="Whether we recommend this parlay")
    ev_pct: float = Field(..., description="Expected Value percentage")
    true_probability: float = Field(..., ge=0, le=1)
    implied_probability: float = Field(..., ge=0, le=1)
    confidence_interval: tuple[float, float] = Field(
        ..., description="95% confidence interval on probability"
    )
    fair_odds: str = Field(..., description="Fair odds based on true probability (e.g., +245)")
    sportsbook_odds: str = Field(..., description="Actual sportsbook odds (e.g., +354)")
    correlation_multiplier: float = Field(
        ..., description="How much correlation helps/hurts (>1 = helps)"
    )
    tail_risk_factor: float = Field(..., description="Inverse of nu (1/nu)")
    simulation_time_ms: float
    explanation: ParlayExplanation
    legs: List[ParlayLegRequest]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Kelly Criterion suggestion
    kelly_stake_pct: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Suggested bankroll % to wager (Kelly Criterion)"
    )

    # @validator("recommended")
    # def check_recommendation_logic(cls, v, values):
    #     """Ensure recommendation is based on positive EV."""
    #     if v and values.get("ev_pct", 0) <= 0:
    #         raise ValueError("Cannot recommend bet with non-positive EV")
    #     return v

    class Config:
        schema_extra = {
            "example": {
                "parlay_id": "sgp_abc123",
                "game_id": "nfl_2026_01_05_sea_lar",
                "recommended": True,
                "ev_pct": 4.2,
                "true_probability": 0.29,
                "implied_probability": 0.22,
                "confidence_interval": (0.24, 0.34),
                "fair_odds": "+245",
                "sportsbook_odds": "+354",
                "correlation_multiplier": 1.15,
                "tail_risk_factor": 0.20,
                "simulation_time_ms": 45.3,
                "kelly_stake_pct": 0.032,
                "explanation": {
                    "overall_confidence": 0.78,
                    "factors": [],
                    "regime_detected": "normal",
                    "regime_reasoning": "Standard game script",
                },
                "legs": [],
                "created_at": "2026-01-05T18:00:00Z",
            }
        }


class SlipBuilderResponse(BaseModel):
    """SlipBuilder clipboard data and deep links."""

    clipboard_text: str = Field(..., description="Text to copy to clipboard")
    game_page_deeplink: str = Field(..., description="Deep link to game page")
    fallback_web_url: str = Field(..., description="Web URL if deep link fails")
    instructions: str = Field(..., description="User-facing instructions")

    class Config:
        schema_extra = {
            "example": {
                "clipboard_text": "My SmartParlay: Stafford Over 265.5 Pass Yds, Kupp Anytime TD",
                "game_page_deeplink": "draftkings://sportsbook/game/nfl_sea_lar",
                "fallback_web_url": "https://sportsbook.draftkings.com/game/nfl/sea-lar",
                "instructions": "Picks copied! Tap to open DraftKings and add legs manually.",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    message: str
    detail: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "error": "Validation Error",
                "message": "Invalid player_id format",
                "detail": {"field": "legs[0].player_id", "reason": "UUID format required"},
                "timestamp": "2026-01-05T18:00:00Z",
            }
        }
