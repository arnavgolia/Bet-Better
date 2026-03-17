"""
Compatibility Engine for Auto-Parlay System
Defines rules for which props can be combined together
Handles correlation and conflict detection
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from app.services.auto_parlay.candidate_generator import PropCandidate

logger = logging.getLogger(__name__)


class RuleAction(str, Enum):
    """What to do when a rule matches"""
    FORBID = "forbid"  # Cannot combine these props
    WARN = "warn"  # Can combine but note the issue
    PENALIZE = "penalize"  # Reduce parlay score
    BONUS = "bonus"  # Increase parlay score (positive correlation)


@dataclass
class CompatibilityRule:
    """Defines a relationship between two props"""
    name: str
    condition: callable  # Function that takes (PropCandidate, PropCandidate) -> bool
    action: RuleAction
    severity: float  # 0-1, how much to penalize/bonus score
    reason: str


@dataclass
class Violation:
    """Represents a rule violation"""
    leg1_index: int
    leg2_index: int
    rule_name: str
    reason: str
    severity: float


@dataclass
class CompatibilityReport:
    """Report on parlay leg compatibility"""
    compatible: bool
    score: float  # 0-1, overall compatibility score
    violations: List[Violation]
    warnings: List[str]
    bonuses: List[str]


class CompatibilityEngine:
    """Checks if props can be combined in a parlay"""

    def __init__(self):
        self.rules = self._build_rules()

    def _build_rules(self) -> List[CompatibilityRule]:
        """Build all compatibility rules"""

        return [
            # ===== FORBIDDEN COMBINATIONS =====

            CompatibilityRule(
                name="same_prop_opposite_direction",
                condition=lambda a, b: (
                    a.player_id == b.player_id and
                    a.stat_type == b.stat_type and
                    a.recommended_direction != b.recommended_direction
                ),
                action=RuleAction.FORBID,
                severity=1.0,
                reason="Cannot bet both over and under on same prop"
            ),

            CompatibilityRule(
                name="duplicate_prop",
                condition=lambda a, b: (
                    a.player_id == b.player_id and
                    a.stat_type == b.stat_type and
                    a.recommended_direction == b.recommended_direction
                ),
                action=RuleAction.FORBID,
                severity=1.0,
                reason="Cannot bet same prop twice"
            ),

            # ===== NEGATIVE CORRELATIONS (PENALIZE) =====

            CompatibilityRule(
                name="qb_yards_vs_opponent_blowout",
                condition=lambda a, b: (
                    'passing_yards' in a.stat_type and
                    'spread' in b.stat_type and
                    a.player and b.game_id == a.game_id and
                    # Check if QB's team is big underdog
                    a.recommended_direction == 'over'
                    # Would need to check if team is underdog by >10
                ),
                action=RuleAction.PENALIZE,
                severity=0.4,
                reason="QB unlikely to throw much if team is losing badly"
            ),

            CompatibilityRule(
                name="rb_yards_vs_team_passing_heavy",
                condition=lambda a, b: (
                    'rushing_yards' in a.stat_type and
                    'passing_yards' in b.stat_type and
                    a.game_id == b.game_id and
                    a.recommended_direction == 'over' and
                    b.recommended_direction == 'over'
                ),
                action=RuleAction.PENALIZE,
                severity=0.25,
                reason="Run-heavy and pass-heavy game scripts conflict"
            ),

            CompatibilityRule(
                name="multiple_tds_same_game",
                condition=lambda a, b: (
                    a.game_id == b.game_id and
                    'td' in a.stat_type.lower() and
                    'td' in b.stat_type.lower() and
                    a.player_id != b.player_id
                ),
                action=RuleAction.PENALIZE,
                severity=0.15,
                reason="Multiple TD scorers from same game reduces independence"
            ),

            # ===== POSITIVE CORRELATIONS (BONUS) =====

            CompatibilityRule(
                name="qb_wr_same_team",
                condition=lambda a, b: (
                    'passing' in a.stat_type and
                    'receiving' in b.stat_type and
                    a.player and b.player and
                    a.player.team_id == b.player.team_id and
                    a.recommended_direction == 'over' and
                    b.recommended_direction == 'over'
                ),
                action=RuleAction.BONUS,
                severity=-0.2,  # Negative severity = bonus
                reason="QB passing yards positively correlated with WR receiving yards"
            ),

            CompatibilityRule(
                name="rb_yards_team_spread",
                condition=lambda a, b: (
                    'rushing_yards' in a.stat_type and
                    'spread' in b.stat_type and
                    a.player and a.game_id == b.game_id and
                    a.recommended_direction == 'over'
                    # Would check if betting on RB's team to cover
                ),
                action=RuleAction.BONUS,
                severity=-0.15,
                reason="RB success correlated with team winning/covering"
            ),

            CompatibilityRule(
                name="player_td_team_total",
                condition=lambda a, b: (
                    'td' in a.stat_type.lower() and
                    'total' in b.stat_type and
                    a.game_id == b.game_id and
                    b.recommended_direction == 'over'
                ),
                action=RuleAction.BONUS,
                severity=-0.1,
                reason="Player TD correlated with high-scoring game"
            ),

            CompatibilityRule(
                name="cross_sport_independence",
                condition=lambda a, b: (
                    a.sport != b.sport
                ),
                action=RuleAction.BONUS,
                severity=-0.1,
                reason="Cross-sport bets are independent (variance bonus)"
            ),

            # ===== WARNINGS (NO SCORE IMPACT) =====

            CompatibilityRule(
                name="weather_impact_passing",
                condition=lambda a, b: (
                    a.game_id == b.game_id and
                    a.weather_impact and a.weather_impact < -0.1 and
                    'passing' in a.stat_type
                ),
                action=RuleAction.WARN,
                severity=0.0,
                reason="Bad weather may impact passing props in this game"
            ),

            CompatibilityRule(
                name="injury_concern",
                condition=lambda a, b: (
                    a.player and a.player.injury_status in ['questionable', 'probable']
                ),
                action=RuleAction.WARN,
                severity=0.0,
                reason=f"Player has injury designation"
            ),
        ]

    def check_compatibility(
        self,
        legs: List[PropCandidate]
    ) -> CompatibilityReport:
        """
        Check if all legs are compatible with each other

        Args:
            legs: List of PropCandidate objects

        Returns:
            CompatibilityReport with violations, warnings, and score
        """
        violations = []
        warnings = []
        bonuses = []
        compatibility_score = 1.0

        # Check each pair of legs
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                leg_a = legs[i]
                leg_b = legs[j]

                # Apply all rules
                for rule in self.rules:
                    try:
                        if rule.condition(leg_a, leg_b):
                            if rule.action == RuleAction.FORBID:
                                violations.append(Violation(
                                    leg1_index=i,
                                    leg2_index=j,
                                    rule_name=rule.name,
                                    reason=rule.reason,
                                    severity=rule.severity
                                ))

                            elif rule.action == RuleAction.WARN:
                                warnings.append(f"Legs {i+1} and {j+1}: {rule.reason}")

                            elif rule.action == RuleAction.PENALIZE:
                                compatibility_score *= (1 - rule.severity)

                            elif rule.action == RuleAction.BONUS:
                                compatibility_score *= (1 + abs(rule.severity))
                                bonuses.append(f"Legs {i+1} and {j+1}: {rule.reason}")

                    except Exception as e:
                        logger.warning(f"Rule {rule.name} failed: {e}")
                        continue

        return CompatibilityReport(
            compatible=len(violations) == 0,
            score=max(0.0, min(2.0, compatibility_score)),  # Clamp between 0 and 2
            violations=violations,
            warnings=warnings,
            bonuses=bonuses
        )

    def filter_incompatible_combinations(
        self,
        candidates: List[PropCandidate],
        num_legs: int,
        max_combinations: int = 1000
    ) -> List[Tuple[PropCandidate, ...]]:
        """
        Generate all valid combinations of candidates

        Args:
            candidates: Pool of prop candidates
            num_legs: Number of legs per parlay
            max_combinations: Maximum combinations to generate

        Returns:
            List of valid parlay combinations (tuples of PropCandidates)
        """
        from itertools import combinations

        valid_combos = []

        # Generate all possible combinations
        all_combos = combinations(candidates, num_legs)

        for i, combo in enumerate(all_combos):
            if i >= max_combinations:
                logger.info(f"Reached max combinations limit ({max_combinations})")
                break

            # Check if this combination is compatible
            report = self.check_compatibility(list(combo))

            if report.compatible:
                valid_combos.append(combo)

        logger.info(f"Generated {len(valid_combos)} valid combinations from {len(candidates)} candidates")

        return valid_combos


class CorrelationEngine:
    """Measures correlation between props"""

    # Historical correlation data (would be computed from actual results)
    HISTORICAL_CORRELATIONS = {
        ('passing_yards', 'receiving_yards_same_team'): 0.72,
        ('rushing_yards', 'passing_yards_same_team'): -0.31,
        ('anytime_tds', 'team_total_over'): 0.58,
        ('spread_cover', 'total_over'): 0.12,
        ('qb_passing_yards', 'opponent_pressure'): -0.45,
    }

    def get_correlation(
        self,
        prop1: PropCandidate,
        prop2: PropCandidate
    ) -> float:
        """
        Calculate correlation coefficient between two props

        Returns:
            float between -1 and 1
            -1 = perfect negative correlation
            0 = independent
            +1 = perfect positive correlation
        """

        # Same player props are highly correlated
        if prop1.player_id and prop1.player_id == prop2.player_id:
            return 0.85

        # Different games are weakly correlated
        if prop1.game_id != prop2.game_id:
            return 0.05

        # Different sports are independent
        if prop1.sport != prop2.sport:
            return 0.0

        # Look up historical correlation
        key = self._make_correlation_key(prop1, prop2)
        if key in self.HISTORICAL_CORRELATIONS:
            return self.HISTORICAL_CORRELATIONS[key]

        # Use rule-based estimation
        return self._estimate_correlation(prop1, prop2)

    def _make_correlation_key(
        self,
        prop1: PropCandidate,
        prop2: PropCandidate
    ) -> Tuple[str, str]:
        """Create lookup key for correlation data"""

        type1 = prop1.stat_type
        type2 = prop2.stat_type

        # Add context modifiers
        if prop1.player and prop2.player:
            if prop1.player.team_id == prop2.player.team_id:
                type2 += '_same_team'

        # Alphabetical order for consistency
        if type1 < type2:
            return (type1, type2)
        else:
            return (type2, type1)

    def _estimate_correlation(
        self,
        prop1: PropCandidate,
        prop2: PropCandidate
    ) -> float:
        """Estimate correlation using rules"""

        # QB and WR from same team
        if ('passing' in prop1.stat_type and 'receiving' in prop2.stat_type):
            if prop1.player and prop2.player and prop1.player.team_id == prop2.player.team_id:
                return 0.6

        # RB and team passing (negative)
        if ('rushing' in prop1.stat_type and 'passing' in prop2.stat_type):
            if prop1.game_id == prop2.game_id:
                return -0.3

        # Default: weakly correlated
        return 0.1

    def measure_parlay_correlation(
        self,
        legs: List[PropCandidate]
    ) -> Dict[str, float]:
        """
        Measure overall correlation for a parlay

        Returns:
            {
                'average': float,
                'max': float,
                'min': float,
                'cluster': str  # 'independent', 'weak', 'moderate', 'strong'
            }
        """
        correlations = []

        # Calculate all pairwise correlations
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                corr = self.get_correlation(legs[i], legs[j])
                correlations.append(corr)

        if not correlations:
            return {
                'average': 0.0,
                'max': 0.0,
                'min': 0.0,
                'cluster': 'independent'
            }

        avg_corr = sum(correlations) / len(correlations)
        max_corr = max(correlations)
        min_corr = min(correlations)

        # Classify correlation strength
        if abs(avg_corr) < 0.2:
            cluster = 'independent'
        elif abs(avg_corr) < 0.4:
            cluster = 'weak'
        elif abs(avg_corr) < 0.6:
            cluster = 'moderate'
        else:
            cluster = 'strong'

        return {
            'average': avg_corr,
            'max': max_corr,
            'min': min_corr,
            'cluster': cluster
        }


# Example usage
if __name__ == "__main__":
    # Create mock candidates for testing
    from unittest.mock import Mock

    # Mock game
    game = Mock()
    game.id = "game1"
    game.sport = "NFL"

    # Mock players
    player1 = Mock()
    player1.id = "player1"
    player1.name = "Patrick Mahomes"
    player1.team_id = "KC"
    player1.position = "QB"

    player2 = Mock()
    player2.id = "player2"
    player2.name = "Travis Kelce"
    player2.team_id = "KC"
    player2.position = "TE"

    # Create candidates
    marginal1 = Mock()
    marginal1.id = "m1"
    marginal1.game_id = "game1"
    marginal1.player_id = "player1"
    marginal1.stat_type = "passing_yards"
    marginal1.line = 285.5

    marginal2 = Mock()
    marginal2.id = "m2"
    marginal2.game_id = "game1"
    marginal2.player_id = "player2"
    marginal2.stat_type = "receiving_yards"
    marginal2.line = 75.5

    candidate1 = PropCandidate(marginal1, game, player1)
    candidate1.recommended_direction = "over"

    candidate2 = PropCandidate(marginal2, game, player2)
    candidate2.recommended_direction = "over"

    # Test compatibility
    engine = CompatibilityEngine()
    report = engine.check_compatibility([candidate1, candidate2])

    print(f"Compatible: {report.compatible}")
    print(f"Score: {report.score:.2f}")
    print(f"Violations: {len(report.violations)}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Bonuses: {report.bonuses}")

    # Test correlation
    corr_engine = CorrelationEngine()
    correlation = corr_engine.get_correlation(candidate1, candidate2)
    print(f"\nCorrelation: {correlation:.2f}")
