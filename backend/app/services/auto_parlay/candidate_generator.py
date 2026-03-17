"""
Candidate Generator for Auto-Parlay System
Filters and selects props based on user intent constraints
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging

from app.models.database import PlayerMarginal, Game, Player, Team
from app.services.auto_parlay.intent_parser import UserIntent, PropCategory, GameSelector

logger = logging.getLogger(__name__)


class PropCandidate:
    """Represents a candidate prop for parlay inclusion"""

    def __init__(self, marginal: PlayerMarginal, game: Game, player: Optional[Player] = None):
        self.id = marginal.id
        self.game_id = marginal.game_id
        self.player_id = marginal.player_id
        self.stat_type = marginal.stat_type
        self.line = marginal.line
        self.over_odds = marginal.over_odds
        self.under_odds = marginal.under_odds
        self.over_prob = marginal.over_prob
        self.under_prob = marginal.under_prob

        # Game context
        self.game = game
        self.sport = game.sport
        self.commence_time = game.commence_time

        # Player context
        self.player = player

        # Metadata (will be populated from prop_metadata table)
        self.model_confidence: Optional[float] = None
        self.sharp_percentage: Optional[float] = None
        self.public_percentage: Optional[float] = None
        self.historical_hit_rate: Optional[float] = None
        self.weather_impact: Optional[float] = None
        self.injury_impact: Optional[float] = None

        # Adjustments
        self.confidence_adjustment: float = 0.0
        self.recommended_direction: str = "over"  # or "under"


class CandidateGenerator:
    """Generates filtered candidate props based on user intent"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_candidates(self, intent: UserIntent) -> List[PropCandidate]:
        """
        Main entry point: generate candidate props matching intent

        Args:
            intent: Parsed user intent with constraints

        Returns:
            List of PropCandidate objects
        """
        logger.info(f"Generating candidates for intent: {intent.num_legs} legs, {intent.risk_profile}")

        # Build SQL query based on intent
        query = self._build_base_query(intent)

        # Execute query
        result = await self.session.execute(query)
        rows = result.all()

        logger.info(f"Found {len(rows)} raw candidates from database")

        # Convert to PropCandidate objects
        candidates = []
        for row in rows:
            marginal, game, player = row
            candidate = PropCandidate(marginal, game, player)
            candidates.append(candidate)

        # Apply filters
        candidates = await self._apply_filters(candidates, intent)

        logger.info(f"After filtering: {len(candidates)} candidates remain")

        return candidates

    def _build_base_query(self, intent: UserIntent):
        """Build SQL query based on intent constraints"""

        # Start with base query joining marginals, games, and players
        query = select(PlayerMarginal, Game, Player).join(
            Game, PlayerMarginal.game_id == Game.id
        ).outerjoin(
            Player, PlayerMarginal.player_id == Player.id
        )

        conditions = []

        # === SPORT FILTER ===
        if intent.sports and 'all' not in intent.sports:
            conditions.append(Game.sport.in_(intent.sports))

        # === GAME FILTER ===
        game_conditions = []
        for game_selector in intent.games:
            if game_selector.type == 'all_available':
                # No additional filter
                pass

            elif game_selector.type == 'championship':
                # Would need a championship flag in games table
                # For now, filter by game importance or playoff status
                pass

            elif game_selector.type == 'time_filter':
                if game_selector.filter == 'today':
                    today_start = datetime.now().replace(hour=0, minute=0, second=0)
                    today_end = today_start + timedelta(days=1)
                    game_conditions.append(
                        and_(
                            Game.commence_time >= today_start,
                            Game.commence_time < today_end
                        )
                    )
                elif game_selector.filter == 'tomorrow':
                    tomorrow_start = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
                    tomorrow_end = tomorrow_start + timedelta(days=1)
                    game_conditions.append(
                        and_(
                            Game.commence_time >= tomorrow_start,
                            Game.commence_time < tomorrow_end
                        )
                    )
                elif game_selector.filter == 'week':
                    week_start = datetime.now().replace(hour=0, minute=0, second=0)
                    week_end = week_start + timedelta(days=7)
                    game_conditions.append(
                        and_(
                            Game.commence_time >= week_start,
                            Game.commence_time < week_end
                        )
                    )

        if game_conditions:
            conditions.append(or_(*game_conditions))

        # === PROP TYPE FILTER ===
        if intent.allowed_prop_types and PropCategory.ALL not in intent.allowed_prop_types:
            prop_types = self._expand_prop_categories(intent.allowed_prop_types)
            conditions.append(PlayerMarginal.stat_type.in_(prop_types))

        # === SAME GAME FILTER ===
        if intent.same_game_only and len(intent.games) == 1:
            # Will be handled by limiting to single game_id
            pass

        # === PLAYER WHITELIST ===
        if intent.player_whitelist:
            conditions.append(Player.name.in_(intent.player_whitelist))

        # === PLAYER BLACKLIST ===
        if intent.player_blacklist:
            conditions.append(~Player.name.in_(intent.player_blacklist))

        # === GAME STATUS ===
        # Only include upcoming games
        conditions.append(Game.status == 'scheduled')
        conditions.append(Game.commence_time > datetime.now())

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Order by game time (soonest first)
        query = query.order_by(Game.commence_time)

        # Limit results to prevent overwhelming system
        query = query.limit(500)

        return query

    def _expand_prop_categories(self, categories: List[PropCategory]) -> List[str]:
        """Convert prop categories to actual stat_type values"""

        prop_map = {
            PropCategory.SCORING: [
                'anytime_tds', 'first_td', 'last_td',
                'two_plus_tds', 'three_plus_tds'
            ],
            PropCategory.PASSING: [
                'passing_yards', 'alt_passing_yards', 'passing_tds',
                'alt_passing_tds', 'completions', 'pass_attempts',
                'longest_completion', 'interceptions'
            ],
            PropCategory.RUSHING: [
                'rushing_yards', 'alt_rushing_yards', 'rushing_tds',
                'rush_attempts', 'longest_rush'
            ],
            PropCategory.RECEIVING: [
                'receiving_yards', 'alt_receiving_yards', 'receptions',
                'alt_receptions', 'receiving_tds', 'longest_reception'
            ],
            PropCategory.GAME_LINES: [
                'spread', 'alt_spread', 'total', 'alt_total',
                'moneyline', 'team_total'
            ],
            PropCategory.ALT_LINES: [
                'alt_passing_yards', 'alt_rushing_yards',
                'alt_receiving_yards', 'alt_receptions',
                'alt_spread', 'alt_total'
            ]
        }

        expanded = []
        for category in categories:
            if category in prop_map:
                expanded.extend(prop_map[category])

        return list(set(expanded))  # Remove duplicates

    async def _apply_filters(
        self,
        candidates: List[PropCandidate],
        intent: UserIntent
    ) -> List[PropCandidate]:
        """Apply additional filters and adjustments"""

        filtered = candidates

        # Filter by injury status
        if intent.injury_aware:
            filtered = [c for c in filtered if self._is_player_healthy(c)]

        # Filter by sharp money (if following sharp action)
        if intent.sharp_money_follow:
            filtered = [c for c in filtered if self._has_sharp_support(c)]

        # Apply weather adjustments
        if intent.weather_aware:
            filtered = self._apply_weather_adjustments(filtered)

        # Public fade logic
        if intent.public_fade:
            filtered = self._apply_public_fade(filtered)

        return filtered

    def _is_player_healthy(self, candidate: PropCandidate) -> bool:
        """Check if player is healthy (not injured/out)"""
        if not candidate.player:
            return True  # Game props don't have players

        injury_status = candidate.player.injury_status
        if injury_status in ['out', 'doubtful']:
            return False

        return True

    def _has_sharp_support(self, candidate: PropCandidate) -> bool:
        """Check if sharp money is backing this prop"""
        if not candidate.sharp_percentage:
            return True  # If no data, don't filter out

        # Consider "sharp" if >60% of sharp money is on this side
        return candidate.sharp_percentage > 60

    def _apply_weather_adjustments(
        self,
        candidates: List[PropCandidate]
    ) -> List[PropCandidate]:
        """Adjust confidence based on weather conditions"""

        for candidate in candidates:
            game = candidate.game

            # Check for adverse weather
            if game.wind_mph and game.wind_mph > 15:
                # High wind impacts passing
                if 'passing' in candidate.stat_type:
                    candidate.confidence_adjustment -= 0.15
                    candidate.weather_impact = -0.15

                # High wind reduces kicking accuracy
                if 'field_goal' in candidate.stat_type:
                    candidate.confidence_adjustment -= 0.20
                    candidate.weather_impact = -0.20

            # Check for rain/snow (would need weather conditions field)
            # For now, use precipitation probability
            if game.precipitation_prob and game.precipitation_prob > 0.5:
                # Rain/snow reduces passing efficiency
                if 'passing' in candidate.stat_type or 'receiving' in candidate.stat_type:
                    candidate.confidence_adjustment -= 0.10
                    candidate.weather_impact = -0.10

                # Rain/snow increases rushing
                if 'rushing' in candidate.stat_type:
                    candidate.confidence_adjustment += 0.05
                    candidate.weather_impact = 0.05

        return candidates

    def _apply_public_fade(
        self,
        candidates: List[PropCandidate]
    ) -> List[PropCandidate]:
        """Fade public money - flip to opposite side if heavy public action"""

        adjusted = []
        for candidate in candidates:
            if candidate.public_percentage and candidate.public_percentage > 70:
                # Heavy public on one side - fade it
                # Flip recommended direction
                if candidate.recommended_direction == "over":
                    candidate.recommended_direction = "under"
                else:
                    candidate.recommended_direction = "over"

            adjusted.append(candidate)

        return adjusted


class ConstraintValidator:
    """Validates that intent constraints are feasible"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Validate user intent and return feasibility report

        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'available_props_count': int,
                'available_games': List[Game]
            }
        """
        errors = []
        warnings = []

        # Validate leg count
        if intent.num_legs < 2:
            errors.append("Parlays must have at least 2 legs")
        if intent.num_legs > 20:
            errors.append("Maximum 20 legs allowed")

        # Check game availability
        query = select(Game).where(
            and_(
                Game.status == 'scheduled',
                Game.commence_time > datetime.now()
            )
        )

        if intent.sports and 'all' not in intent.sports:
            query = query.where(Game.sport.in_(intent.sports))

        result = await self.session.execute(query)
        available_games = result.scalars().all()

        if len(available_games) == 0:
            errors.append("No games match your criteria")

        # Count available props
        prop_query = select(PlayerMarginal).join(Game).where(
            and_(
                Game.status == 'scheduled',
                Game.commence_time > datetime.now()
            )
        )

        if intent.sports and 'all' not in intent.sports:
            prop_query = prop_query.where(Game.sport.in_(intent.sports))

        result = await self.session.execute(prop_query)
        available_props = result.scalars().all()
        props_count = len(available_props)

        if props_count < intent.num_legs:
            errors.append(
                f"Only {props_count} props available, but you requested {intent.num_legs} legs. "
                f"Try reducing leg count or expanding filters."
            )

        # Cross-sport correlation warning
        if len(intent.sports) > 1 and intent.correlation_strategy.value == 'positive_correlation':
            warnings.append(
                "Cross-sport parlays cannot be positively correlated. "
                "Adjusting strategy to minimize correlation."
            )

        # SGP constraint
        if intent.same_game_only and len(available_games) > 1:
            warnings.append(
                "Same-game parlay requires selecting a specific game. "
                "Currently multiple games match criteria."
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'available_props_count': props_count,
            'available_games': available_games
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.services.auto_parlay.intent_parser import IntentParser

    async def test_candidate_generation():
        # Setup database
        engine = create_async_engine(str(settings.database_url), echo=False)
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session_maker() as session:
            # Parse intent
            parser = IntentParser()
            intent = parser.parse("Build me a 5-leg parlay for the Super Bowl")

            # Validate
            validator = ConstraintValidator(session)
            validation = await validator.validate(intent)

            print(f"Validation: {validation['valid']}")
            print(f"Errors: {validation['errors']}")
            print(f"Warnings: {validation['warnings']}")
            print(f"Available props: {validation['available_props_count']}")

            if validation['valid']:
                # Generate candidates
                generator = CandidateGenerator(session)
                candidates = await generator.generate_candidates(intent)

                print(f"\nGenerated {len(candidates)} candidates")
                for i, candidate in enumerate(candidates[:5]):
                    print(f"{i+1}. {candidate.player.name if candidate.player else 'Team'} - "
                          f"{candidate.stat_type} {candidate.line}")

    asyncio.run(test_candidate_generation())
