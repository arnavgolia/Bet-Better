# Auto-Parlay Intelligence System - Architecture & Design Plan

**Status**: Planning Phase - DO NOT IMPLEMENT YET
**Date**: February 1, 2026
**Purpose**: Complete system design for natural-language parlay construction

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Missing Prop Coverage Analysis](#missing-prop-coverage-analysis)
3. [Intent → Constraint System](#intent--constraint-system)
4. [Parlay Construction Engine](#parlay-construction-engine)
5. [Prop Normalization & Compatibility Rules](#prop-normalization--compatibility-rules)
6. [Auto-Parlay Scoring System](#auto-parlay-scoring-system)
7. [UX Flow Design](#ux-flow-design)
8. [Edge Cases & Guardrails](#edge-cases--guardrails)
9. [Data Model Changes](#data-model-changes)
10. [Implementation Roadmap](#implementation-roadmap)

---

## 1. System Overview

### 1.1 Core Problem Statement
**Current State**: Users manually select individual props to build parlays
**Desired State**: Users describe what they want in natural language, system auto-builds optimal parlay

### 1.2 Key Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input (NLP)                         │
│  "Build me a safe 5-leg parlay for the Super Bowl"             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Intent Parser & Validator                     │
│  Extracts: legs, risk, sport, game, constraints                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Constraint Resolution Engine                    │
│  Converts intent → structured filters & rules                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Candidate Leg Generator                        │
│  Queries DB for all valid props matching constraints           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Correlation & Compatibility Filter                 │
│  Removes incompatible combinations using rule engine           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Parlay Optimizer                             │
│  Scores all combinations, selects optimal based on criteria    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Student-t Copula Analysis                       │
│  Validates correlation, calculates true EV                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Response Generator & Explainer                     │
│  Returns parlay + reasoning + alternatives                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Missing Prop Coverage Analysis

### 2.1 Current Backend Schema Gaps

**Current PropType Enum** (backend/app/models/schemas/parlay.py):
```python
class PropType(str, Enum):
    PASSING_YARDS = "passing_yards"
    RUSHING_YARDS = "rushing_yards"
    RECEIVING_YARDS = "receiving_yards"
    PASSING_TDS = "passing_tds"
    ANYTIME_TDS = "anytime_tds"
    RECEPTIONS = "receptions"
    PASS_ATTEMPTS = "pass_attempts"
    COMPLETIONS = "completions"
    INTERCEPTIONS = "interceptions"
```

**MISSING PROPS (Must Add)**:

#### Player Props - Scoring
```python
FIRST_TD = "first_td"                    # First touchdown scorer
LAST_TD = "last_td"                      # Last touchdown scorer
TWO_PLUS_TDS = "two_plus_tds"            # 2+ touchdowns
THREE_PLUS_TDS = "three_plus_tds"        # 3+ touchdowns
```

#### Player Props - Receiving
```python
ALT_RECEIVING_YARDS = "alt_receiving_yards"  # Alternative lines
LONGEST_RECEPTION = "longest_reception"       # Longest catch
RECEIVING_TDS = "receiving_tds"              # Receiving touchdowns
ALT_RECEPTIONS = "alt_receptions"            # Alternative reception lines
```

#### Player Props - Rushing
```python
ALT_RUSHING_YARDS = "alt_rushing_yards"      # Alternative lines
LONGEST_RUSH = "longest_rush"                 # Longest run
RUSHING_TDS = "rushing_tds"                  # Rushing touchdowns
RUSH_ATTEMPTS = "rush_attempts"               # Number of carries
```

#### Player Props - Passing
```python
ALT_PASSING_YARDS = "alt_passing_yards"      # Alternative lines
ALT_PASSING_TDS = "alt_passing_tds"          # Alternative TD lines
PASS_COMPLETIONS = "pass_completions"         # Completions
LONGEST_COMPLETION = "longest_completion"     # Longest pass
SACKS_TAKEN = "sacks_taken"                  # QB sacks
```

#### Game Props - Spreads
```python
SPREAD = "spread"                            # Point spread
ALT_SPREAD = "alt_spread"                    # Alternative spreads
FIRST_HALF_SPREAD = "first_half_spread"      # 1H spread
SECOND_HALF_SPREAD = "second_half_spread"    # 2H spread
QUARTER_SPREAD = "quarter_spread"            # By quarter
```

#### Game Props - Totals
```python
TOTAL = "total"                              # Game total O/U
ALT_TOTAL = "alt_total"                      # Alternative totals
TEAM_TOTAL = "team_total"                    # Team total O/U
FIRST_HALF_TOTAL = "first_half_total"        # 1H total
SECOND_HALF_TOTAL = "second_half_total"      # 2H total
QUARTER_TOTAL = "quarter_total"              # By quarter
```

#### Game Props - Moneyline
```python
MONEYLINE = "moneyline"                      # Win/loss
FIRST_HALF_MONEYLINE = "first_half_ml"       # 1H winner
SECOND_HALF_MONEYLINE = "second_half_ml"     # 2H winner
```

#### Special Props
```python
FIRST_SCORE = "first_score"                  # Team to score first
WINNING_MARGIN = "winning_margin"            # Margin of victory
TOTAL_DRIVES = "total_drives"                # Number of drives
TOTAL_PUNTS = "total_punts"                  # Punts in game
```

### 2.2 Database Schema Extension

**New Table Required**: `alt_lines`
```sql
CREATE TABLE alt_lines (
    id UUID PRIMARY KEY,
    prop_id UUID REFERENCES player_marginals(id),
    line_value DECIMAL,              -- Alternative line (e.g., 55.5 instead of 49.5)
    over_odds INTEGER,               -- Odds for over
    under_odds INTEGER,              -- Odds for under
    line_type VARCHAR(50),           -- 'main', 'alt_high', 'alt_low'
    created_at TIMESTAMP
);
```

**Extend Existing**: `player_marginals`
```sql
ALTER TABLE player_marginals ADD COLUMN prop_category VARCHAR(50);
-- Values: 'player_scoring', 'player_receiving', 'player_rushing',
--         'player_passing', 'game_spread', 'game_total', 'game_moneyline'
```

**New Table**: `game_props`
```sql
CREATE TABLE game_props (
    id UUID PRIMARY KEY,
    game_id UUID REFERENCES games(id),
    prop_type VARCHAR(50),           -- PropType enum value
    team_id UUID REFERENCES teams(id) NULL,  -- For team-specific props
    line DECIMAL NULL,               -- Line value (null for moneyline)
    over_odds INTEGER NULL,
    under_odds INTEGER NULL,
    favorite_odds INTEGER NULL,      -- For spreads/ML
    underdog_odds INTEGER NULL,
    created_at TIMESTAMP
);
```

### 2.3 Ingestion Script Updates

**New Script**: `backend/scripts/ingest_game_props.py`
```python
# Pseudo-implementation structure
def ingest_game_props(game_id: str):
    """Fetch and store game-level props (spread, total, ML)"""

    # Fetch from FanDuel API
    game_props = fanduel_api.get_game_markets(game_id)

    # Parse spreads
    for spread in game_props['spreads']:
        store_prop(
            prop_type='spread',
            team_id=spread['team_id'],
            line=spread['line'],
            odds=spread['odds']
        )

    # Parse alternate spreads
    for alt_spread in game_props['alt_spreads']:
        store_prop(
            prop_type='alt_spread',
            team_id=alt_spread['team_id'],
            line=alt_spread['line'],
            odds=alt_spread['odds']
        )

    # Similar for totals, moneylines, etc.
```

**Update Existing**: `backend/scripts/ingest_fanduel_data.py`
```python
# Add to STAT_MAP
STAT_MAP = {
    # Existing...
    "player_pass_yds": "passing_yards",
    "player_pass_tds": "passing_tds",
    "player_rush_yds": "rushing_yards",
    "player_reception_yds": "receiving_yards",
    "player_anytime_td": "anytime_tds",

    # NEW ADDITIONS
    "player_first_td": "first_td",
    "player_last_td": "last_td",
    "player_alt_rec_yds": "alt_receiving_yards",
    "player_longest_rec": "longest_reception",
    "player_rec_tds": "receiving_tds",
    "player_alt_rush_yds": "alt_rushing_yards",
    "player_longest_rush": "longest_rush",
    "player_rush_tds": "rushing_tds",
    "player_alt_pass_yds": "alt_passing_yards",
    "player_longest_pass": "longest_completion",
    "player_sacks": "sacks_taken",
    # ... etc for all new props
}

# Add handler for alternate lines
def process_alternate_lines(prop_data, player_id, stat_type):
    """Store multiple line options for same prop"""
    main_line = prop_data['main_line']
    alt_lines = prop_data.get('alt_lines', [])

    # Store main
    store_marginal(player_id, stat_type, main_line, 'main')

    # Store alternates
    for alt in alt_lines:
        store_alt_line(player_id, stat_type, alt['line'], alt['odds'])
```

---

## 3. Intent → Constraint System

### 3.1 Intent Parser Architecture

**Input**: Natural language string
**Output**: Structured constraint object

#### 3.1.1 Intent Categories

```typescript
interface UserIntent {
  // Core Requirements
  num_legs: number;                    // 2-20 legs
  risk_profile: RiskProfile;           // 'safe' | 'balanced' | 'aggressive' | 'degen'

  // Scope Filters
  sports: Sport[];                     // ['NFL', 'NBA', 'NHL', etc.]
  games: GameSelector[];               // Specific games or 'all'

  // Prop Preferences
  allowed_prop_types: PropCategory[];  // Which types of props to consider
  exclude_prop_types: PropCategory[];  // Explicitly banned props

  // Correlation Preferences
  correlation_strategy: CorrelationStrategy;  // How to handle correlation
  same_game_only: boolean;             // SGP constraint

  // Advanced Filters
  target_odds_min: number | null;      // Minimum total odds (e.g., +400)
  target_odds_max: number | null;      // Maximum total odds (e.g., +1200)
  player_whitelist: string[];          // Specific players to include
  player_blacklist: string[];          // Players to avoid
  team_whitelist: string[];            // Specific teams
  team_blacklist: string[];            // Teams to avoid

  // Context Modifiers
  weather_aware: boolean;              // Consider weather impact
  injury_aware: boolean;               // Avoid injured players
  sharp_money_follow: boolean;         // Follow sharp action
  public_fade: boolean;                // Fade public bets
}
```

#### 3.1.2 Keyword → Intent Mapping

**Risk Profile Detection**:
```typescript
const RISK_KEYWORDS = {
  safe: ['safe', 'conservative', 'low risk', 'guaranteed', 'sure', 'lock', 'likely'],
  balanced: ['balanced', 'medium', 'moderate', 'normal', 'standard'],
  aggressive: ['risky', 'aggressive', 'high reward', 'longshot', 'bold'],
  degen: ['degen', 'yolo', 'lottery', 'moon shot', 'crazy', 'insane', 'max risk']
};

function detectRiskProfile(text: string): RiskProfile {
  const lower = text.toLowerCase();

  for (const [profile, keywords] of Object.entries(RISK_KEYWORDS)) {
    if (keywords.some(kw => lower.includes(kw))) {
      return profile as RiskProfile;
    }
  }

  return 'balanced';  // Default
}
```

**Leg Count Extraction**:
```typescript
const LEG_PATTERNS = [
  /(\d+)[\s-]leg/i,              // "5-leg" or "5 leg"
  /(\d+)[\s-]pick/i,             // "3-pick"
  /(\d+)[\s]?legger/i,           // "4legger"
];

function extractLegCount(text: string): number | null {
  for (const pattern of LEG_PATTERNS) {
    const match = text.match(pattern);
    if (match) return parseInt(match[1]);
  }

  // Check for word forms
  const wordToNum = {
    'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
  };

  for (const [word, num] of Object.entries(wordToNum)) {
    if (new RegExp(`\\b${word}\\b`, 'i').test(text)) {
      return num;
    }
  }

  return null;  // User must specify
}
```

**Game/Event Detection**:
```typescript
const EVENT_KEYWORDS = {
  'super bowl': { type: 'championship', sport: 'NFL', special: true },
  'world series': { type: 'championship', sport: 'MLB', special: true },
  'nba finals': { type: 'championship', sport: 'NBA', special: true },
  'playoffs': { type: 'playoff', special: true },
  'tonight': { type: 'time_filter', filter: 'today' },
  'tomorrow': { type: 'time_filter', filter: 'tomorrow' },
  'this week': { type: 'time_filter', filter: 'week' },
  'sunday': { type: 'day_filter', day: 0 },
  'monday night': { type: 'time_filter', filter: 'monday_night_football' },
};

function detectGameScope(text: string): GameSelector {
  const lower = text.toLowerCase();

  // Check for special events
  for (const [keyword, config] of Object.entries(EVENT_KEYWORDS)) {
    if (lower.includes(keyword)) {
      return config;
    }
  }

  // Check for team names (requires fuzzy matching)
  const mentionedTeams = extractTeamNames(text);
  if (mentionedTeams.length > 0) {
    return { type: 'team_filter', teams: mentionedTeams };
  }

  return { type: 'all_available' };
}
```

**Prop Type Preference Detection**:
```typescript
const PROP_TYPE_KEYWORDS = {
  scoring: ['touchdown', 'td', 'score', 'anytime', 'first td', 'last td'],
  passing: ['passing', 'pass yards', 'completions', 'quarterback', 'qb'],
  rushing: ['rushing', 'rush yards', 'carries', 'running back', 'rb'],
  receiving: ['receiving', 'rec yards', 'receptions', 'catches', 'wide receiver', 'wr'],
  game_lines: ['spread', 'moneyline', 'total', 'over under', 'game line'],
  alt_lines: ['alt', 'alternative', 'boosted', 'higher line', 'lower line'],
};

function detectPropPreferences(text: string): PropCategory[] {
  const lower = text.toLowerCase();
  const preferences: PropCategory[] = [];

  for (const [category, keywords] of Object.entries(PROP_TYPE_KEYWORDS)) {
    if (keywords.some(kw => lower.includes(kw))) {
      preferences.push(category as PropCategory);
    }
  }

  // If no specific preferences, allow all
  if (preferences.length === 0) {
    return ['all'];
  }

  return preferences;
}
```

**Correlation Strategy Detection**:
```typescript
function detectCorrelationStrategy(text: string, riskProfile: RiskProfile): CorrelationStrategy {
  const lower = text.toLowerCase();

  // Explicit mentions
  if (lower.includes('uncorrelated') || lower.includes('independent')) {
    return 'minimize_correlation';
  }
  if (lower.includes('correlated') || lower.includes('same game')) {
    return 'maximize_correlation';
  }
  if (lower.includes('cross game') || lower.includes('different games')) {
    return 'cross_game';
  }

  // Infer from risk profile
  switch (riskProfile) {
    case 'safe':
      return 'positive_correlation';  // Things that move together (safer)
    case 'aggressive':
    case 'degen':
      return 'minimize_correlation';  // Independent bets (higher variance)
    default:
      return 'neutral';
  }
}
```

#### 3.1.3 Complete Intent Parser Implementation

```typescript
class IntentParser {
  parse(userInput: string): UserIntent {
    // Extract all components
    const numLegs = this.extractLegCount(userInput) || 5;  // Default to 5
    const riskProfile = this.detectRiskProfile(userInput);
    const sports = this.detectSports(userInput);
    const games = this.detectGameScope(userInput);
    const propPrefs = this.detectPropPreferences(userInput);
    const correlationStrategy = this.detectCorrelationStrategy(userInput, riskProfile);

    // Advanced context detection
    const weatherAware = /weather|rain|snow|wind|dome/i.test(userInput);
    const sharpMoneyFollow = /sharp|wiseguy|professional|smart money/i.test(userInput);
    const publicFade = /fade|public|square|casual/i.test(userInput);

    // Construct full intent
    return {
      num_legs: numLegs,
      risk_profile: riskProfile,
      sports: sports,
      games: games,
      allowed_prop_types: propPrefs,
      exclude_prop_types: [],
      correlation_strategy: correlationStrategy,
      same_game_only: /same game|sgp/i.test(userInput),
      target_odds_min: this.extractTargetOdds(userInput, 'min'),
      target_odds_max: this.extractTargetOdds(userInput, 'max'),
      player_whitelist: this.extractPlayerNames(userInput),
      player_blacklist: this.extractBlacklistedPlayers(userInput),
      team_whitelist: [],
      team_blacklist: [],
      weather_aware: weatherAware,
      injury_aware: true,  // Always check injuries
      sharp_money_follow: sharpMoneyFollow,
      public_fade: publicFade,
    };
  }

  // Helper methods...
  private extractTargetOdds(text: string, type: 'min' | 'max'): number | null {
    // Match patterns like "+400", "at least +500", "under +1000"
    const patterns = {
      min: /at least \+(\d+)|minimum \+(\d+)|over \+(\d+)/i,
      max: /under \+(\d+)|maximum \+(\d+)|less than \+(\d+)/i,
    };

    const match = text.match(patterns[type]);
    if (match) {
      const odds = parseInt(match[1] || match[2] || match[3]);
      return odds;
    }

    return null;
  }
}
```

#### 3.1.4 Example Intent Parsing

**Input 1**: "Build me a 5-leg parlay for the Super Bowl"
```json
{
  "num_legs": 5,
  "risk_profile": "balanced",
  "sports": ["NFL"],
  "games": [{ "type": "championship", "sport": "NFL", "special": true }],
  "allowed_prop_types": ["all"],
  "correlation_strategy": "neutral",
  "same_game_only": false
}
```

**Input 2**: "Give me a super safe money parlay"
```json
{
  "num_legs": 5,
  "risk_profile": "safe",
  "sports": ["all"],
  "games": [{ "type": "all_available" }],
  "allowed_prop_types": ["all"],
  "correlation_strategy": "positive_correlation",
  "target_odds_min": null,
  "target_odds_max": 300
}
```

**Input 3**: "Make me a high-risk, high-reward 8-leg cross-game NFL parlay with only passing touchdowns"
```json
{
  "num_legs": 8,
  "risk_profile": "aggressive",
  "sports": ["NFL"],
  "games": [{ "type": "all_available" }],
  "allowed_prop_types": ["passing"],
  "correlation_strategy": "cross_game",
  "same_game_only": false,
  "target_odds_min": 1000
}
```

**Input 4**: "Build a cross-sport parlay (NFL + NBA) that follows sharp money"
```json
{
  "num_legs": 5,
  "risk_profile": "balanced",
  "sports": ["NFL", "NBA"],
  "games": [{ "type": "all_available" }],
  "allowed_prop_types": ["all"],
  "correlation_strategy": "cross_sport",
  "sharp_money_follow": true
}
```

### 3.2 Constraint Validator

```typescript
class ConstraintValidator {
  validate(intent: UserIntent): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate leg count
    if (intent.num_legs < 2) {
      errors.push("Parlays must have at least 2 legs");
    }
    if (intent.num_legs > 20) {
      errors.push("Maximum 20 legs allowed");
    }

    // Check game availability
    if (intent.games.length === 0) {
      errors.push("No games match your criteria");
    }

    // Cross-sport correlation warning
    if (intent.sports.length > 1 && intent.correlation_strategy === 'maximize_correlation') {
      warnings.push("Cross-sport parlays cannot be correlated");
      intent.correlation_strategy = 'minimize_correlation';
    }

    // SGP constraint
    if (intent.same_game_only && intent.games.length > 1) {
      errors.push("Same-game parlay requires exactly one game");
    }

    // Odds target conflicts
    if (intent.target_odds_min && intent.target_odds_max) {
      if (intent.target_odds_min > intent.target_odds_max) {
        errors.push("Minimum odds cannot exceed maximum odds");
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      adjusted_intent: intent
    };
  }
}
```

---

## 4. Parlay Construction Engine

### 4.1 Candidate Generation

```typescript
class CandidateGenerator {
  async generateCandidates(intent: UserIntent): Promise<PropCandidate[]> {
    // Build SQL query based on intent
    const query = this.buildQuery(intent);

    // Fetch all matching props
    const allProps = await db.query(query);

    // Apply filters
    let candidates = allProps;

    // Filter by injury status
    if (intent.injury_aware) {
      candidates = candidates.filter(p => !p.player?.injured);
    }

    // Filter by sharp money
    if (intent.sharp_money_follow) {
      candidates = candidates.filter(p => p.sharp_percentage > 60);
    }

    // Filter by public fade
    if (intent.public_fade) {
      candidates = candidates.filter(p => p.public_percentage > 70);
      // Flip to opposite side
      candidates = candidates.map(p => ({
        ...p,
        recommended_direction: p.recommended_direction === 'over' ? 'under' : 'over'
      }));
    }

    // Weather adjustments
    if (intent.weather_aware) {
      candidates = this.applyWeatherAdjustments(candidates);
    }

    return candidates;
  }

  private buildQuery(intent: UserIntent): SQLQuery {
    const conditions = [];

    // Sport filter
    if (intent.sports.length > 0 && !intent.sports.includes('all')) {
      conditions.push(`sport IN (${intent.sports.map(s => `'${s}'`).join(',')})`);
    }

    // Game filter
    if (intent.games.some(g => g.type === 'championship')) {
      conditions.push(`game.is_playoff = true AND game.round = 'championship'`);
    }

    // Prop type filter
    if (!intent.allowed_prop_types.includes('all')) {
      const propTypes = this.expandPropCategories(intent.allowed_prop_types);
      conditions.push(`prop_type IN (${propTypes.map(t => `'${t}'`).join(',')})`);
    }

    // Team filters
    if (intent.team_whitelist.length > 0) {
      conditions.push(`team_id IN (${intent.team_whitelist.join(',')})`);
    }

    return {
      table: 'player_marginals',
      joins: ['games', 'teams', 'players'],
      where: conditions.join(' AND '),
      orderBy: 'expected_value DESC'
    };
  }

  private applyWeatherAdjustments(candidates: PropCandidate[]): PropCandidate[] {
    return candidates.map(c => {
      if (c.game?.weather?.includes('rain') || c.game?.weather?.includes('snow')) {
        // Downgrade passing, upgrade rushing
        if (c.stat_type.includes('passing')) {
          c.confidence_adjustment = -0.15;
        }
        if (c.stat_type.includes('rushing')) {
          c.confidence_adjustment = +0.10;
        }
      }

      if (c.game?.weather?.includes('wind')) {
        // Downgrade long passes and kicking
        if (c.stat_type === 'longest_completion' || c.stat_type === 'field_goal') {
          c.confidence_adjustment = -0.20;
        }
      }

      return c;
    });
  }
}
```

### 4.2 Leg Compatibility & Filtering

```typescript
interface CompatibilityRule {
  condition: (leg1: PropCandidate, leg2: PropCandidate) => boolean;
  action: 'forbid' | 'warn' | 'penalize';
  severity: number;  // 0-1, how much to penalize score
  reason: string;
}

const COMPATIBILITY_RULES: CompatibilityRule[] = [
  // Same player, opposite directions
  {
    condition: (a, b) =>
      a.player_id === b.player_id &&
      a.stat_type === b.stat_type &&
      a.direction !== b.direction,
    action: 'forbid',
    severity: 1.0,
    reason: "Cannot bet both over and under on same prop"
  },

  // Negative correlation: QB yards vs opponent blowout
  {
    condition: (a, b) =>
      a.stat_type === 'passing_yards' &&
      b.stat_type === 'spread' &&
      a.team_id !== b.team_id &&
      b.line > 10 &&  // Big underdog
      a.direction === 'over',
    action: 'penalize',
    severity: 0.4,
    reason: "QB unlikely to throw much if team is getting blown out"
  },

  // Positive correlation: RB rushing yards + team spread cover
  {
    condition: (a, b) =>
      a.stat_type === 'rushing_yards' &&
      b.stat_type === 'spread' &&
      a.team_id === b.team_id &&
      a.direction === 'over' &&
      b.direction === 'cover',
    action: 'warn',
    severity: -0.2,  // Negative = bonus
    reason: "RB success correlated with team winning"
  },

  // Same game, multiple TDs
  {
    condition: (a, b) =>
      a.game_id === b.game_id &&
      a.stat_type === 'anytime_tds' &&
      b.stat_type === 'anytime_tds' &&
      a.player_id !== b.player_id,
    action: 'penalize',
    severity: 0.15,
    reason: "Multiple TD scorers from same game reduces independence"
  },

  // Cross-sport is independent (bonus)
  {
    condition: (a, b) => a.sport !== b.sport,
    action: 'warn',
    severity: -0.1,
    reason: "Cross-sport bets are uncorrelated (variance bonus)"
  },

  // Star player prop + team total
  {
    condition: (a, b) =>
      a.player?.is_star &&
      b.stat_type === 'team_total' &&
      a.team_id === b.team_id,
    action: 'penalize',
    severity: 0.25,
    reason: "Star performance heavily impacts team total"
  },

  // Weather impact on outdoor passing
  {
    condition: (a, b) =>
      a.game?.weather?.includes('rain') &&
      a.game?.venue_type === 'outdoor' &&
      a.stat_type.includes('passing'),
    action: 'penalize',
    severity: 0.3,
    reason: "Bad weather reduces passing efficiency"
  },
];

class CompatibilityEngine {
  checkCompatibility(legs: PropCandidate[]): CompatibilityReport {
    const violations: Violation[] = [];
    const warnings: Warning[] = [];
    let compatibilityScore = 1.0;

    // Check each pair
    for (let i = 0; i < legs.length; i++) {
      for (let j = i + 1; j < legs.length; j++) {
        const legA = legs[i];
        const legB = legs[j];

        // Apply all rules
        for (const rule of COMPATIBILITY_RULES) {
          if (rule.condition(legA, legB)) {
            if (rule.action === 'forbid') {
              violations.push({
                leg1: i,
                leg2: j,
                reason: rule.reason
              });
            } else if (rule.action === 'warn') {
              warnings.push({
                leg1: i,
                leg2: j,
                reason: rule.reason
              });
            }

            // Adjust score
            compatibilityScore *= (1 - rule.severity);
          }
        }
      }
    }

    return {
      compatible: violations.length === 0,
      score: compatibilityScore,
      violations,
      warnings
    };
  }

  filterIncompatibleCombinations(
    candidates: PropCandidate[],
    numLegs: number
  ): PropCandidate[][] {
    const validCombinations: PropCandidate[][] = [];

    // Generate all possible combinations
    const allCombos = this.generateCombinations(candidates, numLegs);

    // Filter for compatibility
    for (const combo of allCombos) {
      const report = this.checkCompatibility(combo);
      if (report.compatible) {
        validCombinations.push(combo);
      }
    }

    return validCombinations;
  }
}
```

### 4.3 Parlay Scoring & Selection

```typescript
interface ParlayScore {
  overall: number;        // 0-100 composite score
  expected_value: number; // +EV in dollars per $100 bet
  variance: number;       // Statistical variance
  correlation: number;    // -1 to 1 (neg = independent, pos = correlated)
  confidence: number;     // 0-1 model confidence
  risk_adjusted: number;  // Sharpe-like ratio
}

class ParlayScorer {
  score(
    legs: PropCandidate[],
    intent: UserIntent,
    copulaAnalysis: CopulaResult
  ): ParlayScore {

    // 1. Calculate base expected value
    const ev = this.calculateExpectedValue(legs, copulaAnalysis);

    // 2. Measure variance
    const variance = this.calculateVariance(legs, copulaAnalysis);

    // 3. Correlation analysis
    const correlation = this.measureCorrelation(legs, copulaAnalysis);

    // 4. Model confidence
    const confidence = this.aggregateConfidence(legs);

    // 5. Risk-adjusted score (EV / Variance)
    const riskAdjusted = ev / Math.sqrt(variance);

    // 6. Apply intent-based weights
    const overall = this.computeOverallScore(
      ev, variance, correlation, confidence, intent
    );

    return {
      overall,
      expected_value: ev,
      variance,
      correlation,
      confidence,
      risk_adjusted: riskAdjusted
    };
  }

  private computeOverallScore(
    ev: number,
    variance: number,
    correlation: number,
    confidence: number,
    intent: UserIntent
  ): number {
    // Weight factors based on risk profile
    const weights = this.getRiskWeights(intent.risk_profile);

    let score = 0;

    // Safe profile: prioritize confidence and low variance
    // Aggressive profile: prioritize EV and high variance (upside)

    score += weights.ev * Math.max(0, ev);
    score += weights.confidence * confidence * 100;
    score += weights.variance * (1 / (1 + variance));  // Inverse for safe
    score += weights.correlation * this.scoreCorrelation(correlation, intent);

    // Normalize to 0-100
    return Math.min(100, Math.max(0, score));
  }

  private getRiskWeights(profile: RiskProfile): ScoreWeights {
    switch (profile) {
      case 'safe':
        return { ev: 0.2, confidence: 0.5, variance: 0.2, correlation: 0.1 };
      case 'balanced':
        return { ev: 0.35, confidence: 0.35, variance: 0.15, correlation: 0.15 };
      case 'aggressive':
        return { ev: 0.5, confidence: 0.2, variance: 0.2, correlation: 0.1 };
      case 'degen':
        return { ev: 0.6, confidence: 0.1, variance: 0.25, correlation: 0.05 };
    }
  }

  private scoreCorrelation(correlation: number, intent: UserIntent): number {
    // Positive correlation is good for "safe" bets
    // Negative/zero correlation is good for "aggressive" (more variance)

    if (intent.risk_profile === 'safe') {
      return correlation > 0 ? correlation * 100 : 0;
    } else {
      return correlation < 0 ? Math.abs(correlation) * 100 : 50;
    }
  }

  private calculateExpectedValue(
    legs: PropCandidate[],
    copula: CopulaResult
  ): number {
    // Use copula-adjusted probabilities
    const trueProbability = copula.win_probability;
    const impliedProbability = copula.implied_probability;

    // EV = (true_prob * payout) - (1 - true_prob) * stake
    const payout = copula.payout;
    const ev = (trueProbability * payout) - ((1 - trueProbability) * 100);

    return ev;
  }

  private calculateVariance(
    legs: PropCandidate[],
    copula: CopulaResult
  ): number {
    // Higher variance = riskier but higher upside
    // Use copula covariance matrix

    let totalVariance = 0;
    for (let i = 0; i < legs.length; i++) {
      for (let j = 0; j < legs.length; j++) {
        totalVariance += copula.covariance_matrix[i][j];
      }
    }

    return totalVariance;
  }

  private measureCorrelation(
    legs: PropCandidate[],
    copula: CopulaResult
  ): number {
    // Average pairwise correlation from copula
    const correlations = [];

    for (let i = 0; i < legs.length; i++) {
      for (let j = i + 1; j < legs.length; j++) {
        correlations.push(copula.correlation_matrix[i][j]);
      }
    }

    return correlations.reduce((a, b) => a + b, 0) / correlations.length;
  }
}
```

### 4.4 Optimizer Selection Logic

```typescript
class ParlayOptimizer {
  async buildOptimalParlay(intent: UserIntent): Promise<OptimizedParlay> {
    // 1. Generate candidates
    const candidates = await this.candidateGenerator.generateCandidates(intent);

    if (candidates.length < intent.num_legs) {
      throw new Error(`Only ${candidates.length} props available, need ${intent.num_legs}`);
    }

    // 2. Generate valid combinations
    const validCombos = this.compatibilityEngine.filterIncompatibleCombinations(
      candidates,
      intent.num_legs
    );

    // 3. Score each combination
    const scoredParlays: ScoredParlay[] = [];

    for (const combo of validCombos.slice(0, 1000)) {  // Limit for performance
      // Run copula analysis
      const copulaResult = await this.runCopulaAnalysis(combo);

      // Score the parlay
      const score = this.scorer.score(combo, intent, copulaResult);

      // Check if meets odds targets
      if (intent.target_odds_min && copulaResult.total_odds < intent.target_odds_min) {
        continue;
      }
      if (intent.target_odds_max && copulaResult.total_odds > intent.target_odds_max) {
        continue;
      }

      scoredParlays.push({
        legs: combo,
        score,
        copula: copulaResult
      });
    }

    // 4. Sort by overall score
    scoredParlays.sort((a, b) => b.score.overall - a.score.overall);

    // 5. Return top result with alternatives
    const best = scoredParlays[0];
    const alternatives = this.generateAlternatives(best, scoredParlays, intent);

    return {
      primary: best,
      alternatives,
      reasoning: this.explainSelection(best, intent)
    };
  }

  private generateAlternatives(
    best: ScoredParlay,
    allScored: ScoredParlay[],
    intent: UserIntent
  ): Alternative[] {
    const alternatives: Alternative[] = [];

    // Safer version (if original is aggressive)
    if (intent.risk_profile !== 'safe') {
      const safer = allScored.find(p =>
        p.score.variance < best.score.variance &&
        p.score.confidence > best.score.confidence
      );
      if (safer) {
        alternatives.push({
          type: 'safer',
          parlay: safer,
          description: 'Lower variance, higher confidence version'
        });
      }
    }

    // Riskier version (if original is safe)
    if (intent.risk_profile !== 'degen') {
      const riskier = allScored.find(p =>
        p.score.expected_value > best.score.expected_value &&
        p.copula.total_odds > best.copula.total_odds
      );
      if (riskier) {
        alternatives.push({
          type: 'riskier',
          parlay: riskier,
          description: 'Higher potential payout, more variance'
        });
      }
    }

    // Same-game version (if original is cross-game)
    if (!intent.same_game_only) {
      const sgp = allScored.find(p =>
        new Set(p.legs.map(l => l.game_id)).size === 1
      );
      if (sgp) {
        alternatives.push({
          type: 'same_game',
          parlay: sgp,
          description: 'All legs from same game (SGP)'
        });
      }
    }

    return alternatives;
  }
}
```

---

## 5. Prop Normalization & Compatibility Rules

### 5.1 Prop Relationship Matrix

```typescript
// Defines how props interact with each other
const PROP_RELATIONSHIPS: Record<string, PropRelationship[]> = {
  // QB Passing Yards
  'passing_yards_over': {
    positive_correlation: [
      'team_total_over',           // Team scores → QB threw well
      'receiving_yards_over',       // WR catches → QB threw
      'completions_over',           // More completions → more yards
      'spread_cover_favorite',      // Winning team passes more late
    ],
    negative_correlation: [
      'rushing_yards_over_same_team',  // Run-heavy game script
      'time_of_possession_under',      // Quick possessions
      'spread_cover_underdog_opponent', // Getting blown out
    ],
    forbidden: [
      'passing_yards_under',        // Direct conflict
    ]
  },

  // RB Rushing Yards
  'rushing_yards_over': {
    positive_correlation: [
      'spread_cover_favorite',      // Winning = running clock
      'rush_attempts_over',         // Volume indicator
      'team_total_over',            // Scoring = more touches
      'time_of_possession_over',    // Running burns clock
    ],
    negative_correlation: [
      'passing_yards_over_same_team',  // Pass-heavy script
      'spread_cover_underdog',         // Losing teams throw more
      'total_under',                   // Low-scoring = stacked boxes
    ],
    forbidden: [
      'rushing_yards_under',
    ]
  },

  // WR Receiving Yards
  'receiving_yards_over': {
    positive_correlation: [
      'receptions_over',            // Catches = yards
      'passing_yards_over_same_qb', // QB production
      'spread_cover_underdog',      // Losing teams throw more
      'total_over',                 // High-scoring shootout
    ],
    negative_correlation: [
      'rushing_yards_over_same_team',  // Run-heavy
      'weather_bad',                   // Rain/snow
    ],
    forbidden: [
      'receiving_yards_under',
    ]
  },

  // Anytime TD
  'anytime_tds': {
    positive_correlation: [
      'team_total_over',            // Team scores → TD likely
      'receiving_yards_over',       // Yardage + TD (WRs)
      'rushing_yards_over',         // Yardage + TD (RBs)
      'spread_cover',               // Winning = more TDs
    ],
    negative_correlation: [
      'total_under',                // Low-scoring games
      'field_goals_over',           // FGs instead of TDs
    ],
    forbidden: [
      // Multiple anytime TDs same game penalized but not forbidden
    ],
    special_rules: [
      {
        rule: 'redzone_target_bonus',
        condition: 'player.redzone_targets > 5',
        adjustment: +0.15
      }
    ]
  },

  // Spread
  'spread_cover_favorite': {
    positive_correlation: [
      'team_total_over_favorite',   // Favorite scores
      'rushing_yards_over_favorite_rb', // Run clock out
      'total_over',                 // Blowout
    ],
    negative_correlation: [
      'spread_cover_underdog',      // Obviously
      'total_under',                // Close games stay under
    ],
    forbidden: [
      'spread_cover_underdog',
      'spread_opposite_direction',
    ]
  },

  // Totals
  'total_over': {
    positive_correlation: [
      'passing_yards_over_both_teams',
      'receiving_yards_over',
      'anytime_tds',
      'team_total_over',
    ],
    negative_correlation: [
      'rushing_yards_over',         // Ground-and-pound = low score
      'time_of_possession_high',    // Slow pace
      'weather_bad',                // Rain/snow/wind
    ],
    forbidden: [
      'total_under',
    ]
  },

  // Weather-dependent props
  'longest_reception': {
    negative_correlation: [
      'weather_wind',               // Wind kills deep balls
      'weather_rain',
    ],
    positive_correlation: [
      'receiving_yards_over',
      'total_over',
      'weather_dome',               // Indoor = deep shots
    ]
  },

  // Defensive props
  'sacks_taken_over': {
    negative_correlation: [
      'passing_yards_over',         // Hard to throw under pressure
      'completions_over',
      'spread_cover',               // Losing QBs get sacked more
    ],
    positive_correlation: [
      'interceptions_over',         // Pressure = mistakes
      'spread_cover_opponent',
    ]
  },
};
```

### 5.2 Correlation Strength Quantification

```typescript
interface CorrelationData {
  prop1: string;
  prop2: string;
  correlation_coefficient: number;  // -1 to 1
  sample_size: number;
  confidence_interval: [number, number];
}

// Historical correlation data (would be computed from historical results)
const HISTORICAL_CORRELATIONS: CorrelationData[] = [
  {
    prop1: 'passing_yards_over',
    prop2: 'receiving_yards_over_same_team',
    correlation_coefficient: 0.72,
    sample_size: 5000,
    confidence_interval: [0.68, 0.76]
  },
  {
    prop1: 'rushing_yards_over',
    prop2: 'passing_yards_over_same_team',
    correlation_coefficient: -0.31,
    sample_size: 5000,
    confidence_interval: [-0.36, -0.26]
  },
  {
    prop1: 'anytime_tds',
    prop2: 'team_total_over',
    correlation_coefficient: 0.58,
    sample_size: 8000,
    confidence_interval: [0.54, 0.62]
  },
  {
    prop1: 'spread_cover',
    prop2: 'total_over',
    correlation_coefficient: 0.12,
    sample_size: 10000,
    confidence_interval: [0.08, 0.16]
  },
  // ... thousands more from historical data
];

class CorrelationEngine {
  getCorrelation(prop1: PropCandidate, prop2: PropCandidate): number {
    // 1. Check if same player (always correlated)
    if (prop1.player_id === prop2.player_id) {
      return 0.85;  // High correlation for same player
    }

    // 2. Check if different games (low correlation)
    if (prop1.game_id !== prop2.game_id) {
      return 0.05;  // Nearly independent
    }

    // 3. Check if different sports (independent)
    if (prop1.sport !== prop2.sport) {
      return 0.0;
    }

    // 4. Look up historical correlation
    const key = this.makeCorrelationKey(prop1, prop2);
    const historical = HISTORICAL_CORRELATIONS.find(c =>
      (c.prop1 === key.prop1 && c.prop2 === key.prop2) ||
      (c.prop1 === key.prop2 && c.prop2 === key.prop1)
    );

    if (historical) {
      return historical.correlation_coefficient;
    }

    // 5. Use rule-based estimation
    return this.estimateCorrelation(prop1, prop2);
  }

  private estimateCorrelation(p1: PropCandidate, p2: PropCandidate): number {
    const relationships = PROP_RELATIONSHIPS[p1.stat_type];
    if (!relationships) return 0.0;

    // Check positive correlations
    if (relationships.positive_correlation.some(pc => this.matches(p2, pc))) {
      return 0.4;  // Moderate positive
    }

    // Check negative correlations
    if (relationships.negative_correlation.some(nc => this.matches(p2, nc))) {
      return -0.3;  // Moderate negative
    }

    // Default to weakly correlated
    return 0.1;
  }
}
```

### 5.3 Alt Lines Impact on Variance

```typescript
class AltLineAnalyzer {
  analyzeAltLineImpact(mainLine: PropCandidate, altLine: PropCandidate): AltLineImpact {
    const lineDiff = Math.abs(altLine.line - mainLine.line);
    const oddsDiff = altLine.odds - mainLine.odds;

    // Alt lines affect:
    // 1. Win probability
    // 2. Variance
    // 3. Expected value

    let varianceMultiplier = 1.0;
    let evAdjustment = 0;

    if (altLine.line < mainLine.line) {
      // Lower line = easier to hit = lower variance, lower payout
      varianceMultiplier = 1 - (lineDiff / mainLine.line) * 0.3;
      evAdjustment = this.calculateEVChange(oddsDiff);
    } else {
      // Higher line = harder to hit = higher variance, higher payout
      varianceMultiplier = 1 + (lineDiff / mainLine.line) * 0.5;
      evAdjustment = this.calculateEVChange(oddsDiff);
    }

    return {
      variance_multiplier: varianceMultiplier,
      ev_adjustment: evAdjustment,
      recommendation: this.recommendAltLine(altLine, mainLine)
    };
  }

  private recommendAltLine(alt: PropCandidate, main: PropCandidate): string {
    // Compare value
    const mainEV = this.calculateEV(main);
    const altEV = this.calculateEV(alt);

    if (altEV > mainEV + 2) {  // $2 better per $100
      return 'alt_line_better_value';
    } else if (altEV < mainEV - 2) {
      return 'main_line_better_value';
    } else {
      return 'similar_value';
    }
  }
}
```

---

## 6. Auto-Parlay Scoring System

### 6.1 Multi-Dimensional Scoring

```typescript
interface ComprehensiveScore {
  // Core Metrics
  expected_value: number;          // Dollars per $100 (positive = +EV)
  win_probability: number;         // True probability (0-1)
  implied_probability: number;     // Bookmaker's probability (0-1)
  edge: number;                    // win_prob - implied_prob

  // Risk Metrics
  variance: number;                // Statistical variance
  standard_deviation: number;      // Sqrt(variance)
  value_at_risk: number;          // 95th percentile loss
  sharpe_ratio: number;            // EV / StdDev
  kelly_criterion: number;         // Optimal bet size %

  // Correlation Metrics
  average_correlation: number;     // Mean pairwise correlation
  max_correlation: number;         // Highest pair correlation
  correlation_cluster: string;     // 'independent' | 'weak' | 'moderate' | 'strong'

  // Confidence Metrics
  model_confidence: number;        // 0-1 model certainty
  data_quality: number;            // 0-1 input data quality
  sample_size: number;             // Historical observations
  recency_weight: number;          // How recent the data is

  // Market Metrics
  sharp_percentage: number;        // % of sharp money on this side
  public_percentage: number;       // % of public on this side
  line_movement: number;           // How much line has moved
  steam_move: boolean;             // Sudden sharp action

  // Context Metrics
  weather_impact: number;          // -1 to 1 (negative = bad)
  injury_impact: number;           // -1 to 1
  rest_days: number;               // Team rest
  matchup_rating: number;          // 0-100 matchup favorability

  // Composite Scores
  overall_score: number;           // 0-100 weighted composite
  risk_adjusted_score: number;     // Accounting for variance
  intent_alignment: number;        // How well it matches user intent
}

class ComprehensiveScorer {
  scoreParlay(
    legs: PropCandidate[],
    copula: CopulaResult,
    intent: UserIntent
  ): ComprehensiveScore {

    // 1. Core metrics from copula
    const ev = this.calculateEV(copula);
    const winProb = copula.win_probability;
    const impliedProb = copula.implied_probability;
    const edge = winProb - impliedProb;

    // 2. Risk metrics
    const variance = this.calculateVariance(copula);
    const stdDev = Math.sqrt(variance);
    const var95 = this.calculateVaR(copula, 0.95);
    const sharpe = ev / stdDev;
    const kelly = edge / (copula.total_odds / 100);

    // 3. Correlation analysis
    const correlations = this.extractCorrelations(copula);
    const avgCorr = correlations.reduce((a, b) => a + b, 0) / correlations.length;
    const maxCorr = Math.max(...correlations);
    const cluster = this.classifyCorrelation(avgCorr);

    // 4. Confidence aggregation
    const modelConf = this.aggregateModelConfidence(legs);
    const dataQuality = this.assessDataQuality(legs);
    const sampleSize = Math.min(...legs.map(l => l.sample_size || 1000));
    const recency = this.calculateRecencyWeight(legs);

    // 5. Market analysis
    const sharpPct = this.calculateSharpPercentage(legs);
    const publicPct = this.calculatePublicPercentage(legs);
    const lineMove = this.aggregateLineMovement(legs);
    const steam = this.detectSteamMove(legs);

    // 6. Context factors
    const weatherImpact = this.assessWeatherImpact(legs);
    const injuryImpact = this.assessInjuryImpact(legs);
    const restDays = this.getMinRestDays(legs);
    const matchupRating = this.rateMatchups(legs);

    // 7. Composite scores
    const overall = this.calculateOverallScore({
      ev, variance, edge, modelConf, intent
    });
    const riskAdjusted = this.calculateRiskAdjustedScore({
      ev, variance, sharpe, intent
    });
    const intentAlignment = this.scoreIntentAlignment(
      { ev, variance, avgCorr, winProb },
      intent
    );

    return {
      expected_value: ev,
      win_probability: winProb,
      implied_probability: impliedProb,
      edge,
      variance,
      standard_deviation: stdDev,
      value_at_risk: var95,
      sharpe_ratio: sharpe,
      kelly_criterion: kelly,
      average_correlation: avgCorr,
      max_correlation: maxCorr,
      correlation_cluster: cluster,
      model_confidence: modelConf,
      data_quality: dataQuality,
      sample_size: sampleSize,
      recency_weight: recency,
      sharp_percentage: sharpPct,
      public_percentage: publicPct,
      line_movement: lineMove,
      steam_move: steam,
      weather_impact: weatherImpact,
      injury_impact: injuryImpact,
      rest_days: restDays,
      matchup_rating: matchupRating,
      overall_score: overall,
      risk_adjusted_score: riskAdjusted,
      intent_alignment: intentAlignment
    };
  }

  private calculateOverallScore(params: ScoreParams): number {
    const { ev, variance, edge, modelConf, intent } = params;

    // Get weights based on risk profile
    const w = this.getScoreWeights(intent.risk_profile);

    let score = 0;

    // EV component (0-40 points)
    score += Math.min(40, Math.max(0, ev / 5)) * w.ev;

    // Edge component (0-20 points)
    score += (edge * 100) * w.edge;

    // Confidence component (0-20 points)
    score += (modelConf * 20) * w.confidence;

    // Risk component (0-20 points)
    // For safe bets: reward low variance
    // For aggressive: reward high variance (more upside)
    if (intent.risk_profile === 'safe' || intent.risk_profile === 'balanced') {
      score += (20 / (1 + variance)) * w.risk;
    } else {
      score += Math.min(20, variance * 2) * w.risk;
    }

    return Math.min(100, Math.max(0, score));
  }

  private scoreIntentAlignment(
    metrics: { ev: number, variance: number, avgCorr: number, winProb: number },
    intent: UserIntent
  ): number {
    let alignment = 100;

    // Check risk profile alignment
    switch (intent.risk_profile) {
      case 'safe':
        if (metrics.winProb < 0.3) alignment -= 30;  // Too risky
        if (metrics.variance > 5) alignment -= 20;
        break;
      case 'aggressive':
        if (metrics.winProb > 0.5) alignment -= 20;  // Not risky enough
        if (metrics.ev < 10) alignment -= 15;
        break;
      case 'degen':
        if (metrics.winProb > 0.3) alignment -= 40;  // Way too safe
        if (metrics.ev < 20) alignment -= 30;
        break;
    }

    // Check correlation alignment
    if (intent.correlation_strategy === 'maximize_correlation' && metrics.avgCorr < 0.3) {
      alignment -= 25;
    }
    if (intent.correlation_strategy === 'minimize_correlation' && metrics.avgCorr > 0.3) {
      alignment -= 25;
    }

    // Check odds target alignment
    // (would need total odds from copula)

    return Math.max(0, alignment);
  }
}
```

### 6.2 Risk Profile Specific Scoring

```typescript
const RISK_PROFILE_CRITERIA: Record<RiskProfile, ScoringCriteria> = {
  safe: {
    min_win_probability: 0.35,       // At least 35% to win
    max_variance: 3.0,               // Low variance
    min_confidence: 0.7,             // High model confidence
    target_odds_range: [-200, 400], // Lower payouts, higher probability
    preferred_correlation: 'positive', // Things that move together
    preferred_props: ['main_lines', 'unders', 'favorites'],
    max_same_game_legs: 2,           // Limit SGP correlation risk
    weights: {
      ev: 0.20,
      edge: 0.15,
      confidence: 0.40,
      risk: 0.25
    }
  },

  balanced: {
    min_win_probability: 0.25,
    max_variance: 6.0,
    min_confidence: 0.55,
    target_odds_range: [200, 1000],
    preferred_correlation: 'neutral',
    preferred_props: ['all'],
    max_same_game_legs: 3,
    weights: {
      ev: 0.35,
      edge: 0.20,
      confidence: 0.25,
      risk: 0.20
    }
  },

  aggressive: {
    min_win_probability: 0.15,
    max_variance: 12.0,
    min_confidence: 0.40,
    target_odds_range: [800, 5000],
    preferred_correlation: 'negative',  // Independent bets = more variance
    preferred_props: ['alt_lines', 'overs', 'underdogs'],
    max_same_game_legs: 5,
    weights: {
      ev: 0.45,
      edge: 0.25,
      confidence: 0.15,
      risk: 0.15
    }
  },

  degen: {
    min_win_probability: 0.05,        // 5% = 20-to-1 longshot
    max_variance: 50.0,               // Sky-high variance
    min_confidence: 0.25,             // Low bar
    target_odds_range: [2000, 50000], // Huge payouts
    preferred_correlation: 'zero',    // Maximum independence
    preferred_props: ['alt_lines', 'longshots', 'exotics'],
    max_same_game_legs: 8,
    weights: {
      ev: 0.50,
      edge: 0.30,
      confidence: 0.10,
      risk: 0.10  // Don't penalize variance
    }
  }
};
```

---

## 7. UX Flow Design

### 7.1 User Journey

```
┌────────────────────────────────────────────────────────────────┐
│                    1. User Input Phase                         │
│                                                                │
│  [Text Input Box]                                              │
│  "Build me a 5-leg parlay for the Super Bowl"                 │
│                                                                │
│  [Submit Button]                                               │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                 2. Intent Interpretation                        │
│                                                                │
│  "I understand you want:"                                      │
│  ✓ 5 legs                                                      │
│  ✓ Super Bowl only                                             │
│  ✓ Balanced risk profile                                       │
│  ✓ No specific prop preferences                                │
│                                                                │
│  [Looks good] [Modify]                                         │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                3. Building Animation                            │
│                                                                │
│  ⚙️ Analyzing 247 available props...                          │
│  🧮 Running correlation analysis...                           │
│  🎯 Optimizing for balanced risk...                           │
│  ✅ Parlay built!                                             │
│                                                                │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                   4. Parlay Presentation                        │
│                                                                │
│  🎯 Optimized 5-Leg Parlay                                     │
│  Odds: +847 | Win Prob: 24.3% | EV: +$12.40                   │
│                                                                │
│  ┌──────────────────────────────────────────────┐             │
│  │ 1. Patrick Mahomes OVER 285.5 Pass Yards     │             │
│  │    -110 | Confidence: 87%                    │             │
│  │    ℹ️ Why: Mahomes averages 312 yds vs      │             │
│  │       zone coverage, Eagles run 68% zone     │             │
│  └──────────────────────────────────────────────┘             │
│                                                                │
│  ┌──────────────────────────────────────────────┐             │
│  │ 2. Travis Kelce OVER 5.5 Receptions          │             │
│  │    +105 | Confidence: 79%                    │             │
│  │    ℹ️ Why: Kelce sees 9.2 targets in big    │             │
│  │       games, catch rate 82%                  │             │
│  └──────────────────────────────────────────────┘             │
│                                                                │
│  [...3 more legs...]                                           │
│                                                                │
│  📊 Analysis:                                                  │
│  • Correlation: Low (0.18) - legs are mostly independent      │
│  • Sharp Money: 3/5 legs have sharp support                   │
│  • Risk Level: Moderate variance, good upside                 │
│                                                                │
│  [Add to Betslip] [View Alternatives] [Explain More]          │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                  5. Alternatives Section                        │
│                                                                │
│  Not quite right? Try these variations:                       │
│                                                                │
│  ┌─────────────────────────────────────────┐                  │
│  │ 🛡️ SAFER VERSION                       │                  │
│  │ Odds: +412 | Win Prob: 38.1%            │                  │
│  │ Lower variance, higher confidence        │                  │
│  │ [View Details]                           │                  │
│  └─────────────────────────────────────────┘                  │
│                                                                │
│  ┌─────────────────────────────────────────┐                  │
│  │ 🚀 RISKIER VERSION                      │                  │
│  │ Odds: +1543 | Win Prob: 14.2%           │                  │
│  │ Higher payout, more variance             │                  │
│  │ [View Details]                           │                  │
│  └─────────────────────────────────────────┘                  │
│                                                                │
│  ┌─────────────────────────────────────────┐                  │
│  │ 🎮 SAME GAME PARLAY                     │                  │
│  │ Odds: +695 | Win Prob: 28.7%            │                  │
│  │ All legs from this game only             │                  │
│  │ [View Details]                           │                  │
│  └─────────────────────────────────────────┘                  │
│                                                                │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                6. Deep Link to FanDuel                          │
│                                                                │
│  Ready to place this bet?                                      │
│                                                                │
│  [🔗 Open in FanDuel App]                                      │
│  (Auto-fills betslip with your legs)                           │
│                                                                │
│  [📋 Copy Bet Details]                                         │
│  (Copies legs to clipboard)                                    │
│                                                                │
│  [💾 Save for Later]                                           │
│  (Bookmark this parlay)                                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 UI Components

#### Intent Input Component
```tsx
<div className="auto-parlay-builder">
  <h2>Auto-Build Smart Parlay</h2>

  <textarea
    placeholder="Describe your ideal parlay...
Examples:
• Build me a 5-leg parlay for the Super Bowl
• Give me a super safe money parlay
• Make me a high-risk, high-reward NFL parlay
• Build a cross-sport parlay (NFL + NBA)"
    value={userInput}
    onChange={(e) => setUserInput(e.target.value)}
    className="intent-input"
  />

  <div className="quick-presets">
    <button onClick={() => preset('safe')}>🛡️ Safe Money</button>
    <button onClick={() => preset('balanced')}>⚖️ Balanced</button>
    <button onClick={() => preset('risky')}>🚀 High Risk</button>
    <button onClick={() => preset('degen')}>🎰 YOLO</button>
  </div>

  <button onClick={buildParlay} className="build-btn">
    ✨ Build My Parlay
  </button>
</div>
```

#### Leg Explanation Component
```tsx
<div className="parlay-leg">
  <div className="leg-header">
    <span className="leg-number">1</span>
    <span className="player-name">{leg.player}</span>
    <span className="odds">{formatOdds(leg.odds)}</span>
  </div>

  <div className="leg-details">
    <div className="prop-line">
      <span className="direction">{leg.direction.toUpperCase()}</span>
      <span className="line">{leg.line}</span>
      <span className="stat-type">{formatStatType(leg.stat_type)}</span>
    </div>

    <div className="confidence-bar">
      <div className="fill" style={{ width: `${leg.confidence * 100}%` }} />
      <span>{Math.round(leg.confidence * 100)}% confidence</span>
    </div>
  </div>

  <div className="reasoning">
    <button onClick={() => toggleReasoning(leg.id)}>
      ℹ️ Why this leg?
    </button>

    {showReasoning && (
      <div className="reasoning-content">
        <p><strong>Key Factor:</strong> {leg.primary_reason}</p>
        <ul>
          {leg.supporting_factors.map(factor => (
            <li key={factor}>{factor}</li>
          ))}
        </ul>
        <p className="stats">
          • Historical: {leg.historical_hit_rate}% hit rate
          • Matchup: {leg.matchup_advantage}
          • Market: {leg.sharp_percentage}% sharp money
        </p>
      </div>
    )}
  </div>
</div>
```

#### Alternative Parlay Card
```tsx
<div className="alternative-card">
  <div className="alt-header">
    <span className="alt-icon">{alt.icon}</span>
    <h4>{alt.title}</h4>
  </div>

  <div className="alt-stats">
    <div className="stat">
      <span className="label">Odds</span>
      <span className="value">{formatOdds(alt.odds)}</span>
    </div>
    <div className="stat">
      <span className="label">Win Prob</span>
      <span className="value">{(alt.win_prob * 100).toFixed(1)}%</span>
    </div>
    <div className="stat">
      <span className="label">EV</span>
      <span className="value positive">${alt.ev.toFixed(2)}</span>
    </div>
  </div>

  <p className="alt-description">{alt.description}</p>

  <button onClick={() => viewAlt(alt.id)}>
    View Details →
  </button>
</div>
```

### 7.3 Response Generation

```typescript
interface ParlayExplanation {
  summary: string;
  legs: LegExplanation[];
  analysis: AnalysisSection;
  alternatives: Alternative[];
  action_items: ActionItem[];
}

class ExplanationGenerator {
  generateExplanation(
    parlay: ScoredParlay,
    intent: UserIntent
  ): ParlayExplanation {
    return {
      summary: this.generateSummary(parlay, intent),
      legs: parlay.legs.map(leg => this.explainLeg(leg, parlay)),
      analysis: this.generateAnalysis(parlay),
      alternatives: this.describeAlternatives(parlay.alternatives),
      action_items: this.generateActionItems(parlay)
    };
  }

  private generateSummary(parlay: ScoredParlay, intent: UserIntent): string {
    const { score, copula } = parlay;
    const profile = intent.risk_profile;

    let summary = `I've built a ${intent.num_legs}-leg `;

    switch (profile) {
      case 'safe':
        summary += 'conservative parlay with high-confidence picks';
        break;
      case 'balanced':
        summary += 'balanced parlay with good value and reasonable risk';
        break;
      case 'aggressive':
        summary += 'high-upside parlay targeting strong returns';
        break;
      case 'degen':
        summary += 'moonshot parlay with massive payout potential';
        break;
    }

    summary += ` paying ${formatOdds(copula.total_odds)}. `;
    summary += `Your estimated win probability is ${(score.win_probability * 100).toFixed(1)}%, `;
    summary += `with an expected value of ${score.expected_value >= 0 ? '+' : ''}$${score.expected_value.toFixed(2)} per $100 bet.`;

    return summary;
  }

  private explainLeg(leg: PropCandidate, parlay: ScoredParlay): LegExplanation {
    return {
      player: leg.player?.name || 'Team',
      prop: `${leg.direction.toUpperCase()} ${leg.line} ${formatStatType(leg.stat_type)}`,
      odds: leg.odds,
      confidence: leg.model_confidence,
      primary_reason: this.getPrimaryReason(leg),
      supporting_factors: this.getSupportingFactors(leg),
      historical_context: this.getHistoricalContext(leg),
      matchup_analysis: this.getMatchupAnalysis(leg),
      sharp_action: this.getSharpAction(leg),
      correlation_note: this.getCorrelationNote(leg, parlay)
    };
  }

  private getPrimaryReason(leg: PropCandidate): string {
    // Identify the single strongest factor
    const factors = [
      {
        strength: leg.historical_advantage || 0,
        reason: `${leg.player?.name} averages ${leg.historical_average} ${leg.stat_type} in similar matchups`
      },
      {
        strength: leg.matchup_rating || 0,
        reason: `Favorable matchup against opponent's ${leg.opponent_weakness}`
      },
      {
        strength: leg.recent_form || 0,
        reason: `Hot streak: ${leg.recent_performance} in last 5 games`
      },
      {
        strength: leg.sharp_edge || 0,
        reason: `Sharp money heavily backing this side (${leg.sharp_percentage}%)`
      }
    ];

    factors.sort((a, b) => b.strength - a.strength);
    return factors[0].reason;
  }

  private getSupportingFactors(leg: PropCandidate): string[] {
    const factors: string[] = [];

    if (leg.weather_impact) {
      factors.push(`Weather favors this prop: ${leg.weather_description}`);
    }

    if (leg.injury_advantage) {
      factors.push(`Key opponent injury: ${leg.injury_detail}`);
    }

    if (leg.pace_advantage) {
      factors.push(`Game pace projects ${leg.pace_projection} possessions`);
    }

    if (leg.usage_trend) {
      factors.push(`Usage trending up: ${leg.usage_detail}`);
    }

    return factors;
  }
}
```

---

## 8. Edge Cases & Guardrails

### 8.1 Data Availability Issues

**Problem**: User requests props that don't exist yet

```typescript
class DataAvailabilityChecker {
  async validate(intent: UserIntent): Promise<AvailabilityReport> {
    const issues: string[] = [];
    const warnings: string[] = [];

    // Check if games are available
    const games = await this.fetchAvailableGames(intent);
    if (games.length === 0) {
      issues.push("No games match your criteria (check sport, date, teams)");
    }

    // Check if enough props exist
    const propsCount = await this.countAvailableProps(intent);
    if (propsCount < intent.num_legs) {
      issues.push(
        `Only ${propsCount} props available, but you requested ${intent.num_legs} legs. ` +
        `Try: reducing leg count, expanding sport/game selection, or including more prop types.`
      );
    }

    // Check for missing prop types
    const missingTypes = await this.checkMissingPropTypes(intent);
    if (missingTypes.length > 0) {
      warnings.push(
        `These prop types aren't available yet: ${missingTypes.join(', ')}. ` +
        `Using available alternatives.`
      );
    }

    // Check for inactive markets
    const inactiveGames = games.filter(g => g.kickoff_time < Date.now());
    if (inactiveGames.length > 0) {
      warnings.push(
        `Some games have already started. Props may be limited or unavailable.`
      );
    }

    return {
      can_proceed: issues.length === 0,
      issues,
      warnings,
      available_games: games,
      available_props_count: propsCount
    };
  }
}
```

**Fallback Strategy**:
```typescript
class FallbackStrategy {
  async handleInsufficientData(intent: UserIntent): Promise<ParlayResult> {
    // Try to build with fewer legs
    if (intent.num_legs > 2) {
      const reducedIntent = { ...intent, num_legs: intent.num_legs - 1 };
      const result = await this.tryBuild(reducedIntent);

      if (result.success) {
        return {
          ...result,
          note: `Built with ${reducedIntent.num_legs} legs instead of ${intent.num_legs} due to limited prop availability`
        };
      }
    }

    // Try expanding to more games
    if (intent.games.length === 1) {
      const expandedIntent = {
        ...intent,
        games: await this.getSimilarGames(intent.games[0])
      };
      const result = await this.tryBuild(expandedIntent);

      if (result.success) {
        return {
          ...result,
          note: `Expanded to include similar games to meet ${intent.num_legs} legs requirement`
        };
      }
    }

    // Last resort: suggest manual selection
    return {
      success: false,
      error: "Unable to auto-build parlay with current constraints",
      suggestion: "Try manually selecting props or adjusting your criteria"
    };
  }
}
```

### 8.2 Late Odds Movement

**Problem**: Odds change between analysis and user action

```typescript
class OddsMonitor {
  async detectOddsMovement(parlay: ScoredParlay): Promise<MovementReport> {
    const changes: OddsChange[] = [];

    for (const leg of parlay.legs) {
      const currentOdds = await this.fetchLatestOdds(leg.prop_id);

      if (currentOdds !== leg.odds) {
        const movement = currentOdds - leg.odds;
        const direction = movement > 0 ? 'up' : 'down';

        changes.push({
          leg_id: leg.id,
          old_odds: leg.odds,
          new_odds: currentOdds,
          movement,
          direction,
          severity: this.classifyMovementSeverity(movement)
        });
      }
    }

    return {
      has_changes: changes.length > 0,
      changes,
      recommendation: this.getMovementRecommendation(changes)
    };
  }

  private getMovementRecommendation(changes: OddsChange[]): string {
    const majorChanges = changes.filter(c => c.severity === 'major');

    if (majorChanges.length > 0) {
      return 'CAUTION: Significant odds movement detected. Review changes before placing bet.';
    }

    const favorableChanges = changes.filter(c => c.movement > 0);
    if (favorableChanges.length > changes.length / 2) {
      return 'Good news: Odds have generally improved. Consider placing bet soon.';
    }

    return 'Minor odds movement detected. Parlay still valid.';
  }
}
```

**UI Warning**:
```tsx
{oddsMovement.has_changes && (
  <div className="odds-warning">
    <AlertTriangle />
    <div>
      <h4>Odds Have Changed</h4>
      <p>{oddsMovement.recommendation}</p>
      <ul>
        {oddsMovement.changes.map(change => (
          <li key={change.leg_id}>
            {change.leg_name}: {formatOdds(change.old_odds)} → {formatOdds(change.new_odds)}
            <span className={change.movement > 0 ? 'positive' : 'negative'}>
              ({change.movement > 0 ? '+' : ''}{change.movement})
            </span>
          </li>
        ))}
      </ul>
      <button onClick={recalculate}>Recalculate Parlay</button>
    </div>
  </div>
)}
```

### 8.3 Injury Breaking Correlation

**Problem**: Player ruled out after parlay is built

```typescript
class InjuryMonitor {
  async checkInjuryStatus(parlay: ScoredParlay): Promise<InjuryReport> {
    const injuries: InjuryUpdate[] = [];

    for (const leg of parlay.legs) {
      if (!leg.player_id) continue;

      const status = await this.getLatestInjuryStatus(leg.player_id);

      if (status.changed_since(parlay.created_at)) {
        injuries.push({
          player_id: leg.player_id,
          player_name: leg.player?.name,
          old_status: 'active',
          new_status: status.status,
          impact: this.assessImpact(leg, status)
        });
      }
    }

    return {
      has_injuries: injuries.length > 0,
      injuries,
      recommendation: this.getInjuryRecommendation(injuries, parlay)
    };
  }

  private getInjuryRecommendation(
    injuries: InjuryUpdate[],
    parlay: ScoredParlay
  ): string {
    const ruled_out = injuries.filter(i => i.new_status === 'out');

    if (ruled_out.length > 0) {
      return `CRITICAL: ${ruled_out.length} player(s) ruled OUT. Parlay invalidated. Building new parlay...`;
    }

    const questionable = injuries.filter(i => i.new_status === 'questionable');
    if (questionable.length > 0) {
      return `${questionable.length} player(s) now questionable. Monitor closely before placing bet.`;
    }

    return 'No injury concerns.';
  }
}
```

**Auto-Rebuild**:
```typescript
async handleCriticalInjury(
  parlay: ScoredParlay,
  injury: InjuryUpdate
): Promise<UpdatedParlay> {
  // Remove affected leg
  const validLegs = parlay.legs.filter(l => l.player_id !== injury.player_id);

  // Find replacement leg
  const replacementLeg = await this.findReplacementLeg({
    exclude: validLegs,
    intent: parlay.original_intent,
    similar_to: parlay.legs.find(l => l.player_id === injury.player_id)
  });

  // Rebuild with new leg
  const newLegs = [...validLegs, replacementLeg];
  const newParlay = await this.optimizer.buildParlay(parlay.original_intent, newLegs);

  return {
    parlay: newParlay,
    change_note: `Replaced ${injury.player_name} (injured) with ${replacementLeg.player?.name}`
  };
}
```

### 8.4 Props Removed Mid-Build

**Problem**: Sportsbook removes a prop while user is viewing parlay

```typescript
class PropAvailabilityMonitor {
  async validatePropsStillAvailable(parlay: ScoredParlay): Promise<ValidationResult> {
    const unavailable: PropCandidate[] = [];

    for (const leg of parlay.legs) {
      const stillAvailable = await this.checkPropExists(leg.prop_id);

      if (!stillAvailable) {
        unavailable.push(leg);
      }
    }

    if (unavailable.length > 0) {
      return {
        valid: false,
        error: `${unavailable.length} prop(s) no longer available`,
        unavailable_props: unavailable,
        action: 'rebuild'
      };
    }

    return { valid: true };
  }
}
```

### 8.5 Regulatory Restrictions

**Problem**: Some prop types banned in certain states

```typescript
const STATE_RESTRICTIONS: Record<string, PropRestriction> = {
  'NY': {
    banned_props: ['college_props', 'player_props_college'],
    banned_sports: [],
    max_legs: 20,
    notes: 'No college player props allowed'
  },
  'IL': {
    banned_props: ['college_props_in_state'],
    banned_sports: [],
    max_legs: 20,
    notes: 'No props on Illinois college teams'
  },
  'LA': {
    banned_props: ['college_props_in_state'],
    banned_sports: [],
    max_legs: 20,
    notes: 'No props on Louisiana college teams'
  }
};

class RegulatoryFilter {
  filterByState(candidates: PropCandidate[], userState: string): PropCandidate[] {
    const restrictions = STATE_RESTRICTIONS[userState];
    if (!restrictions) return candidates;

    return candidates.filter(prop => {
      // Check banned prop types
      if (restrictions.banned_props.includes(prop.prop_type)) {
        return false;
      }

      // Check banned sports
      if (restrictions.banned_sports.includes(prop.sport)) {
        return false;
      }

      // State-specific rules (e.g., IL college teams)
      if (restrictions.banned_props.includes('college_props_in_state')) {
        if (prop.is_college && prop.team?.state === userState) {
          return false;
        }
      }

      return true;
    });
  }
}
```

---

## 9. Data Model Changes

### 9.1 New Database Tables

**Table: `auto_parlay_requests`**
```sql
CREATE TABLE auto_parlay_requests (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    raw_input TEXT,                    -- Original user request
    parsed_intent JSONB,               -- Structured intent object
    created_at TIMESTAMP DEFAULT NOW(),

    -- Results
    primary_parlay_id UUID,
    alternatives JSONB,                -- Array of alternative parlay IDs

    -- Metrics
    build_time_ms INTEGER,             -- How long it took
    candidates_considered INTEGER,
    combinations_scored INTEGER,

    -- Status
    status VARCHAR(50),                -- 'success' | 'failed' | 'insufficient_data'
    error_message TEXT
);
```

**Table: `built_parlays`**
```sql
CREATE TABLE built_parlays (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES auto_parlay_requests(id),

    -- Parlay composition
    legs JSONB,                        -- Array of leg objects
    num_legs INTEGER,

    -- Scores
    overall_score DECIMAL,
    expected_value DECIMAL,
    win_probability DECIMAL,
    variance DECIMAL,
    correlation DECIMAL,
    confidence DECIMAL,

    -- Copula results
    copula_result JSONB,

    -- Metadata
    risk_profile VARCHAR(50),
    intent_alignment DECIMAL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- User actions
    user_viewed BOOLEAN DEFAULT FALSE,
    user_accepted BOOLEAN DEFAULT FALSE,
    user_modified BOOLEAN DEFAULT FALSE,
    placed_at TIMESTAMP
);
```

**Table: `parlay_leg_explanations`**
```sql
CREATE TABLE parlay_leg_explanations (
    id UUID PRIMARY KEY,
    parlay_id UUID REFERENCES built_parlays(id),
    leg_index INTEGER,

    -- Explanation content
    primary_reason TEXT,
    supporting_factors JSONB,          -- Array of strings
    historical_context TEXT,
    matchup_analysis TEXT,
    sharp_action TEXT,

    -- Factors
    historical_advantage DECIMAL,
    matchup_rating DECIMAL,
    sharp_percentage DECIMAL,
    weather_impact DECIMAL,
    injury_impact DECIMAL
);
```

### 9.2 Extended Models

**Extend: `player_marginals`**
```sql
ALTER TABLE player_marginals ADD COLUMN prop_category VARCHAR(50);
ALTER TABLE player_marginals ADD COLUMN historical_hit_rate DECIMAL;
ALTER TABLE player_marginals ADD COLUMN sharp_percentage DECIMAL;
ALTER TABLE player_marginals ADD COLUMN public_percentage DECIMAL;
ALTER TABLE player_marginals ADD COLUMN line_opened DECIMAL;
ALTER TABLE player_marginals ADD COLUMN line_current DECIMAL;
ALTER TABLE player_marginals ADD COLUMN steam_move BOOLEAN DEFAULT FALSE;
```

**New: `prop_metadata`**
```sql
CREATE TABLE prop_metadata (
    prop_id UUID PRIMARY KEY REFERENCES player_marginals(id),

    -- Historical performance
    last_5_games JSONB,
    season_average DECIMAL,
    career_average DECIMAL,
    vs_opponent_average DECIMAL,

    -- Matchup data
    opponent_rank_vs_position INTEGER,
    opponent_yards_allowed DECIMAL,
    pace_factor DECIMAL,

    -- Usage trends
    target_share DECIMAL,
    snap_percentage DECIMAL,
    redzone_usage DECIMAL,

    -- Model outputs
    projected_value DECIMAL,
    projection_confidence DECIMAL,

    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal**: Get all prop types ingesting correctly

- [ ] Extend `PropType` enum with all missing types
- [ ] Create `alt_lines` table
- [ ] Create `game_props` table
- [ ] Write `ingest_game_props.py` script
- [ ] Update `ingest_fanduel_data.py` with new STAT_MAP entries
- [ ] Test ingestion on Super Bowl game
- [ ] Verify all prop types appear in database

**Deliverables**:
- Database fully populated with all FanDuel prop types
- At least 200+ props available for Super Bowl
- TD scorer props displaying correctly

---

### Phase 2: Intent Parser (Week 3)
**Goal**: Natural language → structured intent

- [ ] Build `IntentParser` class
- [ ] Implement keyword detection (risk, legs, games, etc.)
- [ ] Build `ConstraintValidator`
- [ ] Create test suite with 50+ example phrases
- [ ] Build `/api/parse-intent` endpoint
- [ ] Create UI input component with suggestions

**Deliverables**:
- Can parse 90%+ of reasonable user requests
- Validates and adjusts impossible constraints
- Returns structured intent JSON

---

### Phase 3: Candidate Generation (Week 4)
**Goal**: Filter props based on intent

- [ ] Build `CandidateGenerator` class
- [ ] Implement SQL query builder
- [ ] Add weather adjustment logic
- [ ] Add sharp money filter
- [ ] Add injury filter
- [ ] Test with various intents

**Deliverables**:
- Returns relevant props for any valid intent
- Respects all filters and constraints
- Performance <500ms for most queries

---

### Phase 4: Correlation & Compatibility (Week 5-6)
**Goal**: Define relationships between props

- [ ] Create `PROP_RELATIONSHIPS` matrix
- [ ] Build `CompatibilityEngine`
- [ ] Implement all compatibility rules
- [ ] Create `CorrelationEngine`
- [ ] Compute historical correlation data
- [ ] Build test suite for edge cases

**Deliverables**:
- All major prop relationships defined
- Can filter incompatible combinations
- Correlation scores accurate

---

### Phase 5: Scoring & Optimization (Week 7-8)
**Goal**: Rank and select best parlays

- [ ] Build `ComprehensiveScorer` class
- [ ] Implement multi-dimensional scoring
- [ ] Create risk profile weights
- [ ] Build `ParlayOptimizer`
- [ ] Integrate with existing copula analysis
- [ ] Add alternative generation logic

**Deliverables**:
- Can score any valid parlay combination
- Selects optimal parlay for each risk profile
- Generates useful alternatives

---

### Phase 6: Explanation & UX (Week 9-10)
**Goal**: User-facing interface

- [ ] Build `ExplanationGenerator` class
- [ ] Create parlay presentation UI
- [ ] Build leg reasoning components
- [ ] Add alternative cards
- [ ] Implement "building" animation
- [ ] Add FanDuel deep link integration

**Deliverables**:
- Beautiful, informative parlay display
- Clear explanations for each leg
- Smooth user experience

---

### Phase 7: Edge Cases & Polish (Week 11-12)
**Goal**: Handle failures gracefully

- [ ] Build `DataAvailabilityChecker`
- [ ] Implement `OddsMonitor`
- [ ] Create `InjuryMonitor`
- [ ] Add regulatory filters
- [ ] Build fallback strategies
- [ ] Add comprehensive error messages

**Deliverables**:
- Handles missing data gracefully
- Monitors for changes before bet placement
- State-compliant prop filtering

---

### Phase 8: Testing & Optimization (Week 13-14)
**Goal**: Production-ready

- [ ] Load testing (1000+ concurrent requests)
- [ ] Optimize database queries
- [ ] Cache frequent lookups
- [ ] Add request rate limiting
- [ ] Build admin dashboard for monitoring
- [ ] Create user feedback loop

**Deliverables**:
- Can handle production load
- Sub-2-second response times
- Monitoring and alerting in place

---

## Summary

This architecture provides a complete, production-ready system for:

1. ✅ **Full Prop Coverage**: All FanDuel prop types (player, game, alt lines)
2. ✅ **Natural Language Input**: Parse user intent from conversational requests
3. ✅ **Intelligent Construction**: Auto-build optimal parlays based on risk tolerance
4. ✅ **Correlation Modeling**: Understand and manage prop relationships
5. ✅ **Multi-Dimensional Scoring**: EV, variance, confidence, market factors
6. ✅ **Risk Profiles**: Safe → Degen with appropriate strategies
7. ✅ **Explainability**: Clear reasoning for every leg selection
8. ✅ **Edge Case Handling**: Injuries, odds movement, data availability
9. ✅ **Cross-Game & Cross-Sport**: Support for any combination
10. ✅ **Production-Ready**: Scalable, monitored, error-handled

The system is designed to be the **core differentiator** of SmartParlay - the feature that makes it indispensable.

---

**END OF ARCHITECTURE DOCUMENT**

This plan should be reviewed by:
- ML/Data Science team (copula integration, scoring algorithms)
- Backend team (database schema, API endpoints, ingestion scripts)
- Frontend team (UX flow, components, animations)
- Product team (user testing, iteration priorities)

Do not begin implementation until this plan is approved and understood by all teams.
