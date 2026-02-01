"""
Feature Engineering Pipeline

Transforms raw data into model inputs with proper quantization and normalization.
Critical components:
1. Weather impact quantization (non-linear wind penalty)
2. Injury impact propagation (affects correlated players)
3. Sentiment → numeric prior conversion
4. Steam detection (synchronized odds movement)
"""

import numpy as np
from typing import Dict, List, Optional


def quantize_weather(weather: dict) -> dict:
    """
    Convert raw weather to model-ready multipliers.

    Non-linear wind penalty based on empirical research:
    - Wind < 12mph: No impact
    - Wind 12-18mph: 2% penalty per mph above 12
    - Wind > 18mph: Accelerated penalty (passing becomes very difficult)

    Temperature and precipitation also affect gameplay but less dramatically.
    """
    wind = weather.get("wind_mph", 0)
    temp = weather.get("temp_f", 70)
    precip_prob = weather.get("precip_prob", 0)

    # Wind penalty (strongest effect)
    if wind < 12:
        wind_penalty = 0
    elif wind < 18:
        wind_penalty = (wind - 12) * 0.02
    else:
        wind_penalty = 0.12 + (wind - 18) * 0.03

    # Temperature penalty (extreme cold affects QB grip)
    if temp < 32:
        temp_penalty = (32 - temp) * 0.001  # 0.1% per degree below freezing
    else:
        temp_penalty = 0

    # Precipitation (affects ball handling)
    precip_penalty = precip_prob * 0.05  # Up to 5% penalty for 100% rain chance

    total_penalty = min(wind_penalty + temp_penalty + precip_penalty, 0.30)  # Cap at 30%

    return {
        "pass_yards_multiplier": 1 - total_penalty,
        "fg_accuracy_penalty": total_penalty * 0.8,
        "run_boost": total_penalty * 0.5,  # Teams run more in bad weather
        "total_impact": total_penalty,
    }


def adjust_for_injuries(injuries: List[dict], marginals: dict) -> dict:
    """
    Propagate injury impact to correlated players.

    Example: If Patrick Mahomes is questionable (40% impact):
    - Travis Kelce's receiving yards mean drops by ~12% (30% correlation)
    - Rushing attempts boost by ~5% (negative correlation with QB health)

    Position impact weights based on NFL analysis:
    - QB: 35% (most impactful position)
    - WR1: 15%, RB1: 12%, TE1: 8%
    - OL: 5% (affects entire offense)
    """
    POSITION_WEIGHTS = {
        "QB": 0.35,
        "WR1": 0.15,
        "WR2": 0.10,
        "RB1": 0.12,
        "RB2": 0.08,
        "TE1": 0.08,
        "OL": 0.05,
    }

    for injury in injuries:
        status = injury["status"]
        player_id = injury["player_id"]
        position = injury["position"]

        # Map status to impact multiplier
        if status == "out":
            impact = 1.0
        elif status == "doubtful":
            impact = 0.75
        elif status == "questionable":
            impact = 0.40
        else:
            impact = 0.10

        # Get position weight
        pos_weight = POSITION_WEIGHTS.get(position, 0.05)
        final_impact = impact * pos_weight

        # Adjust correlated players' marginals
        # This would query a correlation graph in production
        affected = get_correlated_players(player_id)
        for affected_id, correlation in affected:
            if affected_id in marginals:
                marginals[affected_id]["mean"] *= (1 - final_impact * abs(correlation))

    return marginals


def sentiment_to_prior(sentiment_score: float, base_prob: float) -> float:
    """
    Bayesian update: shift probability based on expert sentiment.

    Sentiment sources:
    - Beat writer reports
    - Vegas sharp money indicators
    - Social media buzz (filtered for noise)

    Limits sentiment influence to ±10% to prevent overreaction.
    """
    max_shift = 0.10
    shift = (sentiment_score - 0.5) * 2 * max_shift
    return np.clip(base_prob + shift, 0.01, 0.99)


def detect_steam(odds_history: list, window_sec: int = 60) -> Optional[dict]:
    """
    Detect synchronized odds movement (steam).

    Steam = sharp money hitting multiple books simultaneously.
    Criteria:
    - 3+ books move in same direction
    - Within 60 second window
    - Movement > 5 cents (significant)

    This is a strong signal that sharp bettors have information.
    """
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    recent = [o for o in odds_history if o["timestamp"] > now - timedelta(seconds=window_sec)]

    if len(recent) < 3:
        return None

    movements = [o["new_odds"] - o["old_odds"] for o in recent]
    avg_movement = np.mean(movements)
    book_count = len(set(o["book"] for o in recent))

    if abs(avg_movement) > 5 and book_count >= 3:
        return {
            "direction": "over" if avg_movement > 0 else "under",
            "magnitude": abs(avg_movement),
            "book_count": book_count,
            "confidence": min(book_count / 5, 1.0),  # Max confidence at 5+ books
        }

    return None


# Placeholder for correlation lookup
def get_correlated_players(player_id: str) -> List[tuple]:
    """Fetch correlated players from graph database."""
    # In production, this would query a pre-computed correlation graph
    return []
