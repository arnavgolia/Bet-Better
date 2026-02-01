/**
 * TypeScript types matching the backend FastAPI schemas
 */

// Team types (from TeamSummary in backend)
export interface Team {
  id: string;
  name: string;
  abbreviation: string;
}

// Venue types (from VenueSummary in backend)
export interface Venue {
  id: string;
  name: string;
  city: string;
  is_dome: boolean;
}

// Weather data directly on Game (not nested)
export interface Game {
  id: string;
  sport: string;
  home_team: Team;
  away_team: Team;
  venue: Venue | null;
  commence_time: string;
  status: string;
  spread: number | null;
  total: number | null;
  temperature_f: number | null;
  wind_mph: number | null;
  precipitation_prob: number | null;
  created_at: string;
}

// Player types (from PlayerResponse in backend)
export interface Player {
  id: string;
  name: string;
  team_id: string;
  team_name: string;
  team_abbreviation: string;
  position: string;
  jersey_number: string | null;
  injury_status: string | null;
  injury_impact: number | null;
}

// Player prop bet (from PropBetResponse in backend)
export interface PlayerProp {
  id: string;
  player_id: string;
  player_name: string;
  game_id: string;
  stat_type: string;
  line: number;
  over_probability: number;
  under_probability: number;
  over_odds: number | null;
  under_odds: number | null;
  mean: number;
  std_dev: number;
}

// Legacy PlayerMarginal (deprecated, use PlayerProp instead)
export interface PlayerMarginal {
  id: string;
  // Use either player_id or player object
  player_id: string;
  player_name: string;
  game_id: string;
  stat_type: string;

  // Stats
  line: number;
  mean: number;
  std_dev: number;

  // Probabilities & Odds
  over_probability: number;
  under_probability: number;
  over_odds: number | null;
  under_odds: number | null;

  // Expanded with player info from backend
  player?: Player;

  // Deprecated/Optional fields to maintain compatibility if needed
  updated_at?: string;
  passing_yards_projection?: number;
  rushing_yards_projection?: number;
  receiving_yards_projection?: number;
}

// Parlay types
export type BetType = "spread" | "total" | "moneyline" | "player_prop";

export type PropType =
  | "pass_yards"
  | "passing_yards"
  | "passing_tds"
  | "rush_yards"
  | "rushing_yards"
  | "receiving_yards"
  | "touchdowns"
  | "receptions"
  | "pass_attempts"
  | "completions"
  | "interceptions"
  | "anytime_tds";

export type PropDirection = "over" | "under";

// ParlayLeg (matches ParlayLegRequest in backend)
export interface ParlayLeg {
  type: BetType;
  team_id?: string;
  player_id?: string;
  stat?: PropType;
  line: number;
  direction?: PropDirection;
  odds: number; // American odds as integer (e.g., -110, +250)
  // Display-only fields (not sent to backend)
  player_name?: string;
  prop_type?: string;
}

export interface ParlayRequest {
  game_id: string;
  legs: ParlayLeg[];
  context?: {
    weather?: {
      wind_mph?: number;
      temp_f?: number;
      precip_prob?: number;
    };
    injuries?: Array<{
      player_id: string;
      status: string;
      impact: number;
    }>;
  };
  sportsbook?: string;
}

export interface ExplanationFactor {
  name: string;
  impact: number;
  direction: string;
  detail: string;
  confidence: number;
}

export interface ParlayExplanation {
  overall_confidence: number;
  factors: ExplanationFactor[];
  regime_detected: string;
  regime_reasoning: string;
}

export interface ParlayRecommendation {
  parlay_id: string;
  game_id: string;
  recommended: boolean;
  ev_pct: number;
  true_probability: number;
  implied_probability: number;
  confidence_interval: [number, number];
  fair_odds: string;
  sportsbook_odds: string;
  correlation_multiplier: number;
  tail_risk_factor: number;
  simulation_time_ms: number;
  explanation: ParlayExplanation;
  legs: ParlayLeg[];
  kelly_stake_pct?: number;
  created_at?: string;
}

// API Response types
export interface ApiError {
  detail: string;
}
