"""
Parlay Scoring and Optimization System
Multi-dimensional scoring with risk profile integration
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import math

from app.services.auto_parlay.candidate_generator import PropCandidate
from app.services.auto_parlay.intent_parser import RiskProfile, UserIntent
from app.services.auto_parlay.compatibility_engine import CompatibilityEngine, CorrelationEngine

logger = logging.getLogger(__name__)


@dataclass
class ParlayScore:
    """Multi-dimensional score for a parlay"""
    overall: float  # 0-100 composite score
    expected_value: float  # Dollars per $100 bet
    win_probability: float  # 0-1 true probability
    implied_probability: float  # 0-1 bookmaker probability
    edge: float  # win_prob - implied_prob
    variance: float  # Statistical variance
    correlation: float  # -1 to 1
    confidence: float  # 0-1 model confidence
    sharpe_ratio: float  # Risk-adjusted return
    intent_alignment: float  # 0-100 how well it matches user intent


@dataclass
class ScoredParlay:
    """A parlay with its score"""
    legs: List[PropCandidate]
    score: ParlayScore
    copula_result: Optional[Dict[str, Any]] = None
    compatibility_score: float = 1.0
    explanation: str = ""


class ParlayScorer:
    """Scores parlays based on multiple factors"""

    def __init__(self):
        self.compatibility_engine = CompatibilityEngine()
        self.correlation_engine = CorrelationEngine()

    def score(
        self,
        legs: List[PropCandidate],
        intent: UserIntent,
        copula_result: Optional[Dict[str, Any]] = None
    ) -> ParlayScore:
        """
        Score a parlay combination

        Args:
            legs: List of props in the parlay
            intent: User's original intent
            copula_result: Results from copula analysis (if available)

        Returns:
            ParlayScore with all metrics
        """

        # If we have copula results, use them
        if copula_result:
            ev = self._calculate_ev_from_copula(copula_result)
            win_prob = copula_result.get('win_probability', 0.0)
            implied_prob = copula_result.get('implied_probability', 0.0)
            variance = copula_result.get('variance', 0.0)
        else:
            # Estimate without copula
            ev, win_prob, implied_prob, variance = self._estimate_metrics(legs)

        edge = win_prob - implied_prob

        # Correlation analysis
        corr_metrics = self.correlation_engine.measure_parlay_correlation(legs)
        correlation = corr_metrics['average']

        # Confidence
        confidence = self._aggregate_confidence(legs)

        # Sharpe ratio (risk-adjusted return)
        sharpe = ev / math.sqrt(variance) if variance > 0 else 0

        # Intent alignment
        intent_alignment = self._score_intent_alignment(
            ev, variance, correlation, win_prob, intent
        )

        # Overall score
        overall = self._compute_overall_score(
            ev, variance, edge, confidence, intent
        )

        return ParlayScore(
            overall=overall,
            expected_value=ev,
            win_probability=win_prob,
            implied_probability=implied_prob,
            edge=edge,
            variance=variance,
            correlation=correlation,
            confidence=confidence,
            sharpe_ratio=sharpe,
            intent_alignment=intent_alignment
        )

    def _calculate_ev_from_copula(self, copula_result: Dict[str, Any]) -> float:
        """Calculate EV from copula analysis"""
        true_prob = copula_result.get('win_probability', 0.0)
        payout = copula_result.get('payout', 0.0)

        # EV = (true_prob * payout) - (1 - true_prob) * stake
        # Assuming $100 stake
        ev = (true_prob * payout) - ((1 - true_prob) * 100)
        return ev

    def _estimate_metrics(
        self,
        legs: List[PropCandidate]
    ) -> Tuple[float, float, float, float]:
        """
        Estimate metrics without copula (fallback)

        Returns:
            (ev, win_prob, implied_prob, variance)
        """
        # Calculate combined probability (assuming independence for simplicity)
        combined_prob = 1.0
        combined_implied_prob = 1.0

        for leg in legs:
            # Use over_prob or under_prob based on direction
            if leg.recommended_direction == "over":
                prob = leg.over_prob or 0.5
                implied = self._odds_to_prob(leg.over_odds or -110)
            else:
                prob = leg.under_prob or 0.5
                implied = self._odds_to_prob(leg.under_odds or -110)

            combined_prob *= prob
            combined_implied_prob *= implied

        # Calculate payout from combined odds
        american_odds = self._prob_to_american_odds(combined_implied_prob)
        payout = self._calculate_payout(american_odds, 100)

        # EV
        ev = (combined_prob * payout) - ((1 - combined_prob) * 100)

        # Variance (simplified)
        variance = combined_prob * (1 - combined_prob) * (payout ** 2)

        return ev, combined_prob, combined_implied_prob, variance

    def _aggregate_confidence(self, legs: List[PropCandidate]) -> float:
        """Aggregate model confidence across all legs"""
        if not legs:
            return 0.0

        confidences = []
        for leg in legs:
            conf = leg.model_confidence or 0.7  # Default confidence
            confidences.append(conf)

        # Use geometric mean (more conservative than arithmetic)
        product = 1.0
        for c in confidences:
            product *= c

        return product ** (1.0 / len(confidences))

    def _compute_overall_score(
        self,
        ev: float,
        variance: float,
        edge: float,
        confidence: float,
        intent: UserIntent
    ) -> float:
        """
        Compute 0-100 composite score

        Weights vary by risk profile
        """
        weights = self._get_score_weights(intent.risk_profile)

        score = 0.0

        # EV component (0-40 points)
        ev_score = min(40, max(0, ev / 5)) * weights['ev']
        score += ev_score

        # Edge component (0-20 points)
        edge_score = (edge * 100) * weights['edge']
        score += edge_score

        # Confidence component (0-20 points)
        confidence_score = (confidence * 20) * weights['confidence']
        score += confidence_score

        # Risk component (0-20 points)
        if intent.risk_profile in [RiskProfile.SAFE, RiskProfile.BALANCED]:
            # Reward low variance
            risk_score = (20 / (1 + variance)) * weights['risk']
        else:
            # Reward high variance (more upside)
            risk_score = min(20, variance * 2) * weights['risk']
        score += risk_score

        return min(100, max(0, score))

    def _get_score_weights(self, profile: RiskProfile) -> Dict[str, float]:
        """Get scoring weights for risk profile"""
        weights_map = {
            RiskProfile.SAFE: {
                'ev': 0.20,
                'edge': 0.15,
                'confidence': 0.40,
                'risk': 0.25
            },
            RiskProfile.BALANCED: {
                'ev': 0.35,
                'edge': 0.20,
                'confidence': 0.25,
                'risk': 0.20
            },
            RiskProfile.AGGRESSIVE: {
                'ev': 0.45,
                'edge': 0.25,
                'confidence': 0.15,
                'risk': 0.15
            },
            RiskProfile.DEGEN: {
                'ev': 0.50,
                'edge': 0.30,
                'confidence': 0.10,
                'risk': 0.10
            }
        }
        return weights_map.get(profile, weights_map[RiskProfile.BALANCED])

    def _score_intent_alignment(
        self,
        ev: float,
        variance: float,
        correlation: float,
        win_prob: float,
        intent: UserIntent
    ) -> float:
        """
        Score how well parlay aligns with user intent

        Returns:
            0-100 score
        """
        alignment = 100.0

        # Check risk profile alignment
        if intent.risk_profile == RiskProfile.SAFE:
            if win_prob < 0.3:
                alignment -= 30
            if variance > 5:
                alignment -= 20
        elif intent.risk_profile == RiskProfile.AGGRESSIVE:
            if win_prob > 0.5:
                alignment -= 20
            if ev < 10:
                alignment -= 15
        elif intent.risk_profile == RiskProfile.DEGEN:
            if win_prob > 0.3:
                alignment -= 40
            if ev < 20:
                alignment -= 30

        # Check correlation alignment
        if intent.correlation_strategy.value == 'positive_correlation':
            if correlation < 0.3:
                alignment -= 25
        elif intent.correlation_strategy.value == 'minimize_correlation':
            if correlation > 0.3:
                alignment -= 25

        return max(0, alignment)

    @staticmethod
    def _odds_to_prob(american_odds: int) -> float:
        """Convert American odds to probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    @staticmethod
    def _prob_to_american_odds(prob: float) -> int:
        """Convert probability to American odds"""
        if prob >= 0.5:
            return int(-100 * prob / (1 - prob))
        else:
            return int(100 * (1 - prob) / prob)

    @staticmethod
    def _calculate_payout(american_odds: int, stake: float) -> float:
        """Calculate payout from American odds"""
        if american_odds > 0:
            return stake * (american_odds / 100)
        else:
            return stake * (100 / abs(american_odds))


class ParlayOptimizer:
    """Finds optimal parlay from candidates"""

    def __init__(self, scorer: ParlayScorer):
        self.scorer = scorer
        self.compatibility_engine = CompatibilityEngine()

    async def build_optimal_parlay(
        self,
        candidates: List[PropCandidate],
        intent: UserIntent,
        max_combinations: int = 1000
    ) -> Dict[str, Any]:
        """
        Build the optimal parlay given candidates and intent

        Args:
            candidates: Pool of props to choose from
            intent: User's intent
            max_combinations: Max combinations to evaluate

        Returns:
            {
                'primary': ScoredParlay,
                'alternatives': List[ScoredParlay],
                'reasoning': str
            }
        """
        logger.info(f"Building optimal parlay from {len(candidates)} candidates")

        if len(candidates) < intent.num_legs:
            raise ValueError(f"Only {len(candidates)} candidates but need {intent.num_legs} legs")

        # Generate valid combinations
        valid_combinations = self.compatibility_engine.filter_incompatible_combinations(
            candidates,
            intent.num_legs,
            max_combinations
        )

        if not valid_combinations:
            raise ValueError("No valid combinations found - all conflict with each other")

        logger.info(f"Evaluating {len(valid_combinations)} valid combinations")

        # Score each combination
        scored_parlays: List[ScoredParlay] = []

        for combo in valid_combinations[:max_combinations]:
            legs = list(combo)

            # Check compatibility score
            compat_report = self.compatibility_engine.check_compatibility(legs)

            # Score the parlay
            score = self.scorer.score(legs, intent, copula_result=None)

            scored_parlay = ScoredParlay(
                legs=legs,
                score=score,
                compatibility_score=compat_report.score
            )

            scored_parlays.append(scored_parlay)

        # Sort by overall score
        scored_parlays.sort(key=lambda p: p.score.overall, reverse=True)

        # Select best
        best = scored_parlays[0]

        # Generate alternatives
        alternatives = self._generate_alternatives(best, scored_parlays, intent)

        # Generate reasoning
        reasoning = self._explain_selection(best, intent)

        return {
            'primary': best,
            'alternatives': alternatives,
            'reasoning': reasoning
        }

    def _generate_alternatives(
        self,
        best: ScoredParlay,
        all_scored: List[ScoredParlay],
        intent: UserIntent
    ) -> List[Dict[str, Any]]:
        """Generate safer/riskier/SGP alternatives"""
        alternatives = []

        # Safer version
        if intent.risk_profile != RiskProfile.SAFE:
            safer = self._find_safer_version(all_scored, best)
            if safer:
                alternatives.append({
                    'type': 'safer',
                    'parlay': safer,
                    'description': 'Lower variance, higher win probability'
                })

        # Riskier version
        if intent.risk_profile != RiskProfile.DEGEN:
            riskier = self._find_riskier_version(all_scored, best)
            if riskier:
                alternatives.append({
                    'type': 'riskier',
                    'parlay': riskier,
                    'description': 'Higher potential payout, more variance'
                })

        # Same-game version
        if not intent.same_game_only:
            sgp = self._find_same_game_version(all_scored)
            if sgp:
                alternatives.append({
                    'type': 'same_game',
                    'parlay': sgp,
                    'description': 'All legs from same game (SGP)'
                })

        return alternatives

    def _find_safer_version(
        self,
        parlays: List[ScoredParlay],
        current: ScoredParlay
    ) -> Optional[ScoredParlay]:
        """Find parlay with lower variance and higher confidence"""
        for parlay in parlays:
            if (parlay.score.variance < current.score.variance and
                parlay.score.confidence > current.score.confidence):
                return parlay
        return None

    def _find_riskier_version(
        self,
        parlays: List[ScoredParlay],
        current: ScoredParlay
    ) -> Optional[ScoredParlay]:
        """Find parlay with higher EV and higher variance"""
        for parlay in parlays:
            if (parlay.score.expected_value > current.score.expected_value and
                parlay.score.variance > current.score.variance):
                return parlay
        return None

    def _find_same_game_version(
        self,
        parlays: List[ScoredParlay]
    ) -> Optional[ScoredParlay]:
        """Find parlay where all legs are from same game"""
        for parlay in parlays:
            game_ids = set(leg.game_id for leg in parlay.legs)
            if len(game_ids) == 1:
                return parlay
        return None

    def _explain_selection(
        self,
        parlay: ScoredParlay,
        intent: UserIntent
    ) -> str:
        """Generate explanation for why this parlay was selected"""
        profile_desc = {
            RiskProfile.SAFE: "conservative picks with high confidence",
            RiskProfile.BALANCED: "balanced value and reasonable risk",
            RiskProfile.AGGRESSIVE: "high-upside targeting strong returns",
            RiskProfile.DEGEN: "moonshot with massive payout potential"
        }

        desc = profile_desc.get(intent.risk_profile, "balanced")

        reasoning = (
            f"I've built a {intent.num_legs}-leg {desc} parlay. "
            f"Your estimated win probability is {parlay.score.win_probability*100:.1f}%, "
            f"with an expected value of ${parlay.score.expected_value:.2f} per $100 bet."
        )

        return reasoning


# Example usage
if __name__ == "__main__":
    from unittest.mock import Mock

    # Create mock candidates
    candidates = []
    for i in range(10):
        marginal = Mock()
        marginal.id = f"m{i}"
        marginal.game_id = "game1"
        marginal.player_id = f"player{i}"
        marginal.stat_type = "passing_yards"
        marginal.line = 250.5 + i * 10
        marginal.over_odds = -110
        marginal.under_odds = -110
        marginal.over_prob = 0.52
        marginal.under_prob = 0.48

        game = Mock()
        game.id = "game1"
        game.sport = "NFL"

        player = Mock()
        player.id = f"player{i}"
        player.team_id = "KC"

        candidate = PropCandidate(marginal, game, player)
        candidate.recommended_direction = "over"
        candidate.model_confidence = 0.75

        candidates.append(candidate)

    # Test scoring
    scorer = ParlayScorer()
    intent = Mock()
    intent.risk_profile = RiskProfile.BALANCED
    intent.num_legs = 5
    intent.correlation_strategy = Mock()
    intent.correlation_strategy.value = 'neutral'

    score = scorer.score(candidates[:5], intent)
    print(f"Overall Score: {score.overall:.1f}")
    print(f"EV: ${score.expected_value:.2f}")
    print(f"Win Prob: {score.win_probability*100:.1f}%")
    print(f"Confidence: {score.confidence:.2f}")
