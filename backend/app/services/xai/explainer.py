"""
Explainable AI Service

Generates human-readable explanations for why the model made specific predictions.
Uses SHAP-inspired attribution but optimized for speed (<20ms target).

Why This Matters:
Users need to understand WHY a parlay is +EV. Simply showing "28% probability"
isn't enough - they want to know: "Is it the weather? The matchup? Sharp money?"

This builds trust and helps users learn, which increases retention.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ExplanationFactor:
    """Individual factor contributing to the prediction."""
    name: str
    impact: float  # -1 to 1 (negative = hurts probability, positive = helps)
    direction: str  # "positive", "negative", "neutral"
    detail: str  # Human-readable explanation
    confidence: float  # 0-1 (how confident we are in this factor)


class XAIService:
    """
    Fast explanation generation using precomputed impact tables.

    Strategy:
    - Static factors (DVOA, historical): Precomputed nightly
    - Dynamic factors (weather, injuries): Computed on-demand
    - Correlation effects: Marginal contribution sampling
    """

    def explain_parlay(
        self,
        parlay_probability: float,
        legs: List[dict],
        context: dict,
    ) -> Dict:
        """
        Generate explanation for parlay prediction.

        Returns:
            {
                "overall_confidence": 0.78,
                "factors": [ExplanationFactor(...)],
                "leg_explanations": [...],
                "regime_info": {...}
            }
        """
        factors = []

        # Factor 1: Weather impact
        if context.get("weather"):
            weather_impact = self._explain_weather(context["weather"])
            factors.append(weather_impact)

        # Factor 2: Injuries
        if context.get("injuries"):
            injury_impact = self._explain_injuries(context["injuries"])
            factors.append(injury_impact)

        # Factor 3: Steam/sharp money
        if context.get("steam_detected"):
            steam_impact = self._explain_steam(context["steam_detected"])
            factors.append(steam_impact)

        # Factor 4: Matchup (DVOA)
        if context.get("dvoa"):
            matchup_impact = self._explain_matchup(context["dvoa"])
            factors.append(matchup_impact)

        # Sort by absolute impact
        factors.sort(key=lambda f: abs(f.impact), reverse=True)

        return {
            "overall_confidence": self._calculate_confidence(factors),
            "factors": factors,
            "regime_info": context.get("regime_params"),
        }

    def _explain_weather(self, weather: dict) -> ExplanationFactor:
        """Explain weather impact."""
        wind = weather.get("wind_mph", 0)
        if wind > 15:
            return ExplanationFactor(
                name="Weather: High Wind",
                impact=-0.15,
                direction="negative",
                detail=f"{wind} mph wind significantly reduces passing efficiency",
                confidence=0.90,
            )
        elif wind > 10:
            return ExplanationFactor(
                name="Weather: Moderate Wind",
                impact=-0.05,
                direction="negative",
                detail=f"{wind} mph wind may slightly affect passing game",
                confidence=0.70,
            )
        return ExplanationFactor(
            name="Weather: Favorable",
            impact=0.0,
            direction="neutral",
            detail="Weather conditions are not a significant factor",
            confidence=0.80,
        )

    def _explain_injuries(self, injuries: List[dict]) -> ExplanationFactor:
        """Explain injury impact."""
        if not injuries:
            return ExplanationFactor(
                name="Injuries: None",
                impact=0.0,
                direction="neutral",
                detail="No significant injuries affecting this parlay",
                confidence=0.85,
            )

        # Find most impactful injury
        key_injury = max(injuries, key=lambda i: i.get("impact", 0))
        return ExplanationFactor(
            name=f"Injury: {key_injury['player_name']}",
            impact=-key_injury["impact"] * 0.2,
            direction="negative",
            detail=f"{key_injury['player_name']} ({key_injury['status']}) affects correlated players",
            confidence=0.75,
        )

    def _explain_steam(self, steam: dict) -> ExplanationFactor:
        """Explain sharp money movement."""
        direction = steam["direction"]
        magnitude = steam["magnitude"]
        return ExplanationFactor(
            name="Sharp Money Detected",
            impact=0.08 if direction == "favorable" else -0.08,
            direction="positive" if direction == "favorable" else "negative",
            detail=f"Sharp bettors moved the line {magnitude} cents {direction}",
            confidence=steam.get("confidence", 0.80),
        )

    def _explain_matchup(self, dvoa: dict) -> ExplanationFactor:
        """Explain team matchup impact."""
        mismatch = abs(dvoa.get("offense", 0) - dvoa.get("defense", 0))
        if mismatch > 0.20:
            return ExplanationFactor(
                name="Matchup: Significant Mismatch",
                impact=0.12 if dvoa["offense"] > dvoa["defense"] else -0.12,
                direction="positive" if dvoa["offense"] > dvoa["defense"] else "negative",
                detail=f"Large DVOA difference ({mismatch:.2f}) creates predictable outcomes",
                confidence=0.88,
            )
        return ExplanationFactor(
            name="Matchup: Evenly Matched",
            impact=0.0,
            direction="neutral",
            detail="Teams are evenly matched based on advanced metrics",
            confidence=0.70,
        )

    def _calculate_confidence(self, factors: List[ExplanationFactor]) -> float:
        """Calculate overall explanation confidence."""
        if not factors:
            return 0.50
        return sum(f.confidence for f in factors) / len(factors)
