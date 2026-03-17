"""
Intent Parser for Auto-Parlay System
Converts natural language user requests into structured constraints
"""

import re
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel


class RiskProfile(str, Enum):
    """Risk tolerance levels"""
    SAFE = "safe"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    DEGEN = "degen"


class CorrelationStrategy(str, Enum):
    """How to handle correlation between legs"""
    POSITIVE_CORRELATION = "positive_correlation"  # Legs that move together (safer)
    MINIMIZE_CORRELATION = "minimize_correlation"  # Independent legs (more variance)
    CROSS_GAME = "cross_game"  # Different games
    CROSS_SPORT = "cross_sport"  # Different sports
    NEUTRAL = "neutral"  # Don't optimize for correlation


class PropCategory(str, Enum):
    """Categories of props"""
    ALL = "all"
    SCORING = "scoring"
    PASSING = "passing"
    RUSHING = "rushing"
    RECEIVING = "receiving"
    GAME_LINES = "game_lines"
    ALT_LINES = "alt_lines"


class GameSelector(BaseModel):
    """How to select games"""
    type: str  # 'all_available', 'championship', 'team_filter', 'time_filter', 'day_filter'
    sport: Optional[str] = None
    teams: Optional[List[str]] = None
    special: bool = False
    filter: Optional[str] = None
    day: Optional[int] = None


class UserIntent(BaseModel):
    """Structured representation of user's parlay request"""

    # Core requirements
    num_legs: int
    risk_profile: RiskProfile

    # Scope filters
    sports: List[str]
    games: List[GameSelector]

    # Prop preferences
    allowed_prop_types: List[PropCategory]
    exclude_prop_types: List[PropCategory] = []

    # Correlation preferences
    correlation_strategy: CorrelationStrategy
    same_game_only: bool = False

    # Advanced filters
    target_odds_min: Optional[int] = None
    target_odds_max: Optional[int] = None
    player_whitelist: List[str] = []
    player_blacklist: List[str] = []
    team_whitelist: List[str] = []
    team_blacklist: List[str] = []

    # Context modifiers
    weather_aware: bool = False
    injury_aware: bool = True  # Always check injuries
    sharp_money_follow: bool = False
    public_fade: bool = False


class IntentParser:
    """Parses natural language into structured UserIntent"""

    # Risk profile keywords
    RISK_KEYWORDS = {
        RiskProfile.SAFE: ['safe', 'conservative', 'low risk', 'guaranteed', 'sure', 'lock', 'likely', 'easy'],
        RiskProfile.BALANCED: ['balanced', 'medium', 'moderate', 'normal', 'standard', 'reasonable'],
        RiskProfile.AGGRESSIVE: ['risky', 'aggressive', 'high reward', 'longshot', 'bold', 'big payout'],
        RiskProfile.DEGEN: ['degen', 'yolo', 'lottery', 'moon shot', 'crazy', 'insane', 'max risk', 'parlay god']
    }

    # Special events
    EVENT_KEYWORDS = {
        'super bowl': {'type': 'championship', 'sport': 'NFL', 'special': True},
        'superbowl': {'type': 'championship', 'sport': 'NFL', 'special': True},
        'world series': {'type': 'championship', 'sport': 'MLB', 'special': True},
        'nba finals': {'type': 'championship', 'sport': 'NBA', 'special': True},
        'finals': {'type': 'championship', 'special': True},
        'playoffs': {'type': 'playoff', 'special': True},
        'tonight': {'type': 'time_filter', 'filter': 'today'},
        'tomorrow': {'type': 'time_filter', 'filter': 'tomorrow'},
        'this week': {'type': 'time_filter', 'filter': 'week'},
        'weekend': {'type': 'time_filter', 'filter': 'weekend'},
        'sunday': {'type': 'day_filter', 'day': 0},
        'monday': {'type': 'day_filter', 'day': 1},
        'monday night': {'type': 'time_filter', 'filter': 'monday_night_football'},
    }

    # Sport keywords
    SPORT_KEYWORDS = {
        'nfl': 'NFL',
        'football': 'NFL',
        'nba': 'NBA',
        'basketball': 'NBA',
        'mlb': 'MLB',
        'baseball': 'MLB',
        'nhl': 'NHL',
        'hockey': 'NHL',
    }

    # Prop type keywords
    PROP_TYPE_KEYWORDS = {
        PropCategory.SCORING: ['touchdown', 'td', 'score', 'anytime', 'first td', 'last td', 'scoring'],
        PropCategory.PASSING: ['passing', 'pass yards', 'completions', 'quarterback', 'qb', 'throw'],
        PropCategory.RUSHING: ['rushing', 'rush yards', 'carries', 'running back', 'rb', 'run'],
        PropCategory.RECEIVING: ['receiving', 'rec yards', 'receptions', 'catches', 'wide receiver', 'wr', 'tight end', 'te'],
        PropCategory.GAME_LINES: ['spread', 'moneyline', 'total', 'over under', 'game line', 'team'],
        PropCategory.ALT_LINES: ['alt', 'alternative', 'boosted', 'higher line', 'lower line'],
    }

    def parse(self, user_input: str) -> UserIntent:
        """
        Main parsing method

        Args:
            user_input: Natural language request from user

        Returns:
            UserIntent: Structured constraints
        """
        # Convert to lowercase for matching
        text_lower = user_input.lower()

        # Extract components
        num_legs = self._extract_leg_count(text_lower) or 5  # Default to 5
        risk_profile = self._detect_risk_profile(text_lower)
        sports = self._detect_sports(text_lower)
        games = self._detect_game_scope(text_lower)
        prop_prefs = self._detect_prop_preferences(text_lower)
        correlation_strategy = self._detect_correlation_strategy(text_lower, risk_profile)

        # Advanced detection
        same_game_only = bool(re.search(r'\b(same game|sgp)\b', text_lower))
        weather_aware = bool(re.search(r'\b(weather|rain|snow|wind|dome)\b', text_lower))
        sharp_money = bool(re.search(r'\b(sharp|wiseguy|professional|smart money)\b', text_lower))
        public_fade = bool(re.search(r'\b(fade|public|square|casual)\b', text_lower))

        # Odds targets
        target_odds_min = self._extract_target_odds(text_lower, 'min')
        target_odds_max = self._extract_target_odds(text_lower, 'max')

        # Player mentions
        player_whitelist = self._extract_player_names(user_input)  # Use original case

        return UserIntent(
            num_legs=num_legs,
            risk_profile=risk_profile,
            sports=sports if sports else ['NFL'],  # Default to NFL
            games=games if games else [GameSelector(type='all_available')],
            allowed_prop_types=prop_prefs if prop_prefs else [PropCategory.ALL],
            correlation_strategy=correlation_strategy,
            same_game_only=same_game_only,
            target_odds_min=target_odds_min,
            target_odds_max=target_odds_max,
            player_whitelist=player_whitelist,
            weather_aware=weather_aware,
            sharp_money_follow=sharp_money,
            public_fade=public_fade,
        )

    def _extract_leg_count(self, text: str) -> Optional[int]:
        """Extract number of legs from text"""
        # Pattern: "5-leg", "5 leg", "5 pick", "five leg"
        patterns = [
            r'(\d+)[\s-]leg',
            r'(\d+)[\s-]pick',
            r'(\d+)[\s]?legger',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        # Check for word forms
        word_to_num = {
            'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }

        for word, num in word_to_num.items():
            if re.search(rf'\b{word}\b', text):
                return num

        return None

    def _detect_risk_profile(self, text: str) -> RiskProfile:
        """Detect risk tolerance from keywords"""
        for profile, keywords in self.RISK_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return profile

        return RiskProfile.BALANCED  # Default

    def _detect_sports(self, text: str) -> List[str]:
        """Detect which sports are mentioned"""
        detected = []
        for keyword, sport in self.SPORT_KEYWORDS.items():
            if keyword in text:
                detected.append(sport)

        # Check for "cross-sport"
        if 'cross' in text and 'sport' in text:
            # Extract multiple sports
            if not detected:
                detected = ['NFL', 'NBA']  # Default multi-sport

        return list(set(detected))  # Remove duplicates

    def _detect_game_scope(self, text: str) -> List[GameSelector]:
        """Detect which games to target"""
        games = []

        # Check for special events
        for keyword, config in self.EVENT_KEYWORDS.items():
            if keyword in text:
                games.append(GameSelector(**config))

        if not games:
            games.append(GameSelector(type='all_available'))

        return games

    def _detect_prop_preferences(self, text: str) -> List[PropCategory]:
        """Detect which prop types user wants"""
        detected = []

        for category, keywords in self.PROP_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                detected.append(category)

        return detected if detected else []

    def _detect_correlation_strategy(
        self,
        text: str,
        risk_profile: RiskProfile
    ) -> CorrelationStrategy:
        """Determine correlation strategy"""

        # Explicit mentions
        if 'uncorrelated' in text or 'independent' in text:
            return CorrelationStrategy.MINIMIZE_CORRELATION
        if 'correlated' in text or 'same game' in text:
            return CorrelationStrategy.POSITIVE_CORRELATION
        if 'cross game' in text or 'different games' in text:
            return CorrelationStrategy.CROSS_GAME
        if 'cross' in text and 'sport' in text:
            return CorrelationStrategy.CROSS_SPORT

        # Infer from risk profile
        if risk_profile == RiskProfile.SAFE:
            return CorrelationStrategy.POSITIVE_CORRELATION
        elif risk_profile in [RiskProfile.AGGRESSIVE, RiskProfile.DEGEN]:
            return CorrelationStrategy.MINIMIZE_CORRELATION
        else:
            return CorrelationStrategy.NEUTRAL

    def _extract_target_odds(self, text: str, type: str) -> Optional[int]:
        """Extract minimum or maximum odds targets"""
        patterns = {
            'min': [
                r'at least \+(\d+)',
                r'minimum \+(\d+)',
                r'over \+(\d+)',
            ],
            'max': [
                r'under \+(\d+)',
                r'maximum \+(\d+)',
                r'less than \+(\d+)',
            ]
        }

        for pattern in patterns[type]:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        return None

    def _extract_player_names(self, text: str) -> List[str]:
        """Extract player names mentioned in request"""
        # This is a simplified version - would need more sophisticated NER
        # For now, look for capitalized words that might be names

        # Common patterns like "with Mahomes" or "include Kelce"
        pattern = r'\b(?:with|include|add|featuring)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        matches = re.findall(pattern, text)

        return matches


# Example usage and testing
if __name__ == "__main__":
    parser = IntentParser()

    # Test cases
    test_inputs = [
        "Build me a 5-leg parlay for the Super Bowl",
        "Give me a super safe money parlay",
        "Make me a high-risk cross-game NFL parlay with only passing touchdowns",
        "Build a cross-sport parlay (NFL + NBA) that follows sharp money",
        "Give me a degen lottery ticket",
        "Build me a same game parlay for tonight with Mahomes and Kelce",
    ]

    for input_text in test_inputs:
        print(f"\nInput: {input_text}")
        intent = parser.parse(input_text)
        print(f"Parsed Intent:")
        print(f"  Legs: {intent.num_legs}")
        print(f"  Risk: {intent.risk_profile}")
        print(f"  Sports: {intent.sports}")
        print(f"  Games: {[g.type for g in intent.games]}")
        print(f"  Props: {intent.allowed_prop_types}")
        print(f"  Correlation: {intent.correlation_strategy}")
        print(f"  Same Game: {intent.same_game_only}")
