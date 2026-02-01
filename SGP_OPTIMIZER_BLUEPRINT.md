# Automated Same-Game Parlay Optimizer - System Blueprint

> A production-grade system for generating +EV Same Game Parlays using Copula-based correlation modeling, real-time odds ingestion, and Explainable AI.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │   Next.js    │  │  React Native│  │   PWA        │                       │
│  │   Web App    │  │  Mobile App  │  │   (Future)   │                       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘                       │
└─────────┼─────────────────┼─────────────────────────────────────────────────┘
          │                 │
          ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Kong / AWS API Gateway  │  Auth (JWT + OAuth)  │  Rate Limiting     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND SERVICES                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Parlay    │  │  Odds      │  │  User      │  │  Affiliate │            │
│  │  Service   │  │  Service   │  │  Service   │  │  Service   │            │
│  │  (Python)  │  │  (Python)  │  │  (Python)  │  │  (Python)  │            │
│  └─────┬──────┘  └─────┬──────┘  └────────────┘  └────────────┘            │
└────────┼───────────────┼────────────────────────────────────────────────────┘
         │               │
         ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID INGESTION LAYER                                    │
│  ┌────────────────────────────┐  ┌────────────────────────────────────┐     │
│  │  WebSocket (Main Lines)    │  │  Smart Polling (Props)             │     │
│  │  ML/Spread/Total - <1s     │  │  30s intervals, triggered on steam │     │
│  └────────────────────────────┘  └────────────────────────────────────┘     │
│  Topics: odds.main, odds.props, stats.live, alerts.steam                    │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DATA & SIMULATION LAYER                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Copula    │  │  Feature   │  │  XAI       │  │  Weather   │            │
│  │  Engine    │  │  Pipeline  │  │  Service   │  │  Service   │            │
│  │  (Python)  │  │  (Python)  │  │  (Python)  │  │  (Go)      │            │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                             │
│  │  Redis     │  │ PostgreSQL │  │ TimescaleDB│                             │
│  │  (Cache)   │  │ (Primary)  │  │ (Time-ser) │                             │
│  └────────────┘  └────────────┘  └────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Language | Responsibility |
|---------|----------|----------------|
| **Parlay Service** | Python | SGP generation, Copula simulation orchestration, +EV calculation |
| **Odds Service** | Python | Real-time odds ingestion via WebSocket (asyncio), line shopping, steam detection |
| **User Service** | Python | Auth, profiles, betting history, preferences |
| **Affiliate Service** | Python | SlipBuilder clipboard fallback, commission tracking, geo-routing |
| **Copula Engine** | Python + JAX | **Student-t Copula** simulations (tail dependence), correlation matrix management |
| **Regime Detector** | Python | Game script classification (Blowout/Shootout/Defensive), conditional correlation |
| **Feature Pipeline** | Python | Weather quantization, injury adjustments, sentiment scoring |
| **XAI Service** | Python | SHAP approximation, explanation generation |
| **Entity Resolution (Rosetta Stone)** | Python | Cross-book player/team name mapping, fuzzy matching |
| **Grading Engine** | Python | Post-game settlement, CLV tracking, ROI calculation |
| **Geo-Compliance** | Python + MaxMind | State-based sportsbook visibility, deep-link routing |

---

## 2. Core Engine Design (The Secret Sauce)

### 2.1 Inputs

```json
{
  "game_id": "nfl_2026_01_05_sea_lar",
  "legs": [
    {"type": "spread", "team": "SEA", "line": 3.5},
    {"type": "player_prop", "player_id": "stafford_01", "stat": "pass_yards", "line": 265.5, "direction": "over"}
  ],
  "context": {
    "weather": {"wind_mph": 12, "temp_f": 55, "precip_prob": 0.1},
    "injuries": [{"player_id": "kupp_01", "status": "questionable", "impact": 0.7}],
    "sentiment_score": 0.65
  }
}
```

### 2.2 Outputs

```json
{
  "parlay_id": "sgp_abc123",
  "recommended": true,
  "ev_pct": 4.2,
  "true_probability": 0.29,
  "implied_probability": 0.22,
  "fair_odds": "+245",
  "sportsbook_odds": "+354",
  "confidence_interval": [0.24, 0.34],
  "legs": [...],
  "explanation": {...}
}
```

### 2.3 Simulation Workflow (Student-t Copula)

> [!IMPORTANT]
> **Why Student-t over Gaussian?** Gaussian Copulas assume tail independence—extreme events aren't correlated. In sports, OT games push ALL stats over together. Student-t captures this "tail dependence" via the ν (degrees of freedom) parameter.

```
1. MARGINAL FITTING (Offline, Daily)
   └─> Fit Beta/Gamma/Weibull distributions per player/stat
   └─> Store in Redis: marginal:{player_id}:{stat} = {dist_type, params}

2. CORRELATION MATRIX (Offline, Weekly + Event-Triggered)
   └─> Compute Kendall's Tau between all variable pairs
   └─> Cholesky decomposition for efficient sampling
   └─> Store in Redis: corr_matrix:{league}:{season} = cholesky_matrix

3. REGIME DETECTION (Real-time, Per Request)
   └─> Classify expected game script: BLOWOUT | SHOOTOUT | DEFENSIVE | NORMAL
   └─> Adjust ν parameter: Lower ν for volatile matchups (more tail risk)
   └─> Boost correlations for regime-specific effects (e.g., garbage time)

4. SIMULATION (Real-time) — **JAX Student-t Copula**
   └─> Generate multivariate normals with Cholesky correlation
   └─> Generate Chi-squared samples for heavy tails
   └─> Convert: t = Z / sqrt(W/ν) → Student-t variates
   └─> Inverse CDF mapping to marginals
   └─> **Target: <50ms on GPU, <150ms on CPU**

5. +EV CALCULATION
   └─> implied_prob = 1 / decimal_odds
   └─> edge = true_prob - implied_prob
   └─> ev_pct = edge / implied_prob * 100
   └─> tail_risk_factor = 1/ν (how "crazy" the game could get)
```

### 2.4 Latency Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| Marginal lookup | <5ms | Redis cache |
| Correlation matrix load | <20ms | Precomputed Cholesky in Redis |
| 10K simulations | <50ms (GPU) / <150ms (CPU) | **JAX JIT-compiled kernel** |
| Full SGP request | <300ms | End-to-end |

---

## 3. Data Models & Schemas

### 3.1 PostgreSQL Tables

```sql
-- Core entities
CREATE TABLE games (
  id UUID PRIMARY KEY,
  sport VARCHAR(10),
  home_team_id UUID REFERENCES teams(id),
  away_team_id UUID REFERENCES teams(id),
  commence_time TIMESTAMPTZ,
  venue_id UUID REFERENCES venues(id),
  status VARCHAR(20)
);

CREATE TABLE players (
  id UUID PRIMARY KEY,
  name VARCHAR(100),
  team_id UUID REFERENCES teams(id),
  position VARCHAR(10),
  injury_status VARCHAR(20),
  injury_impact DECIMAL(3,2)
);

CREATE TABLE player_marginals (
  id UUID PRIMARY KEY,
  player_id UUID REFERENCES players(id),
  stat_type VARCHAR(30),
  dist_type VARCHAR(20),
  params JSONB,
  sample_size INT,
  updated_at TIMESTAMPTZ
);

CREATE TABLE correlation_matrices (
  id UUID PRIMARY KEY,
  league VARCHAR(10),
  season VARCHAR(10),
  matrix_data BYTEA, -- Compressed sparse matrix
  updated_at TIMESTAMPTZ
);

CREATE TABLE parlay_recommendations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  game_id UUID REFERENCES games(id),
  legs JSONB,
  true_prob DECIMAL(5,4),
  ev_pct DECIMAL(5,2),
  explanation JSONB,
  created_at TIMESTAMPTZ
);

-- Entity Resolution (Rosetta Stone) Tables
CREATE TABLE player_mappings (
  internal_id UUID PRIMARY KEY REFERENCES players(id),
  canonical_name VARCHAR(100),
  draftkings_name VARCHAR(100),
  fanduel_name VARCHAR(100),
  betmgm_name VARCHAR(100),
  sportradar_id VARCHAR(50),
  espn_id VARCHAR(50),
  pff_id VARCHAR(50),
  match_confidence DECIMAL(3,2),  -- 0.0-1.0
  needs_review BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMPTZ
);

CREATE TABLE team_mappings (
  internal_id UUID PRIMARY KEY REFERENCES teams(id),
  canonical_name VARCHAR(50),
  abbreviation VARCHAR(5),
  draftkings_name VARCHAR(50),
  fanduel_name VARCHAR(50),
  sportradar_id VARCHAR(50)
);

-- Grading Engine Tables
CREATE TABLE parlay_outcomes (
  id UUID PRIMARY KEY,
  parlay_id UUID REFERENCES parlay_recommendations(id),
  outcome VARCHAR(10),  -- 'win', 'loss', 'push', 'void'
  actual_payout DECIMAL(10,2),
  closing_line_value DECIMAL(5,2),  -- CLV tracking
  graded_at TIMESTAMPTZ
);

CREATE TABLE leg_outcomes (
  id UUID PRIMARY KEY,
  parlay_outcome_id UUID REFERENCES parlay_outcomes(id),
  leg_index INT,
  actual_value DECIMAL(10,2),  -- e.g., actual passing yards
  line_value DECIMAL(10,2),
  outcome VARCHAR(10)
);
```

### 3.2 Redis Keys

```
# Real-time odds (TTL: 60s)
odds:{game_id}:{book}:{market} = {"line": 265.5, "over": -110, "under": -110}

# Best odds across books
best_odds:{game_id}:{market} = {"book": "draftkings", "line": 265.5, "odds": -105}

# Player marginals (TTL: 24h)
marginal:{player_id}:{stat} = {"dist": "gamma", "shape": 2.5, "scale": 85}

# Correlation matrix (TTL: 7d)
corr_matrix:{league}:{season} = <compressed binary>

# Steam alerts (TTL: 5m)
steam:{game_id} = {"direction": "away", "magnitude": 2.5, "timestamp": "..."}

# User session
session:{user_id} = {"preferences": {...}, "bankroll": 1000}

# Entity resolution cache (TTL: 24h)
player_map:{external_source}:{external_id} = {"internal_id": "uuid", "confidence": 0.95}

# Geolocation cache (TTL: 1h)
geo:{ip_hash} = {"state": "NY", "allowed_books": ["draftkings", "fanduel", "caesars"]}
```

### 3.3 Kafka/Redpanda Topics

| Topic | Partitions | Retention | Schema |
|-------|------------|-----------|--------|
| `odds.nfl` | 32 | 7 days | OddsUpdate |
| `odds.nba` | 32 | 7 days | OddsUpdate |
| `stats.live` | 16 | 24 hours | LiveStatEvent |
| `alerts.steam` | 8 | 1 hour | SteamAlert |
| `simulations.requests` | 16 | 1 hour | SimulationRequest |
| `simulations.results` | 16 | 24 hours | SimulationResult |

### 3.4 Example Payloads

**Odds Update (Kafka)**
```json
{
  "event_id": "nfl_2026_01_05_sea_lar",
  "book": "draftkings",
  "market": "player_pass_yards",
  "player_id": "stafford_01",
  "line": 265.5,
  "over_odds": -115,
  "under_odds": -105,
  "timestamp": "2026-01-05T18:00:00Z"
}
```

**XAI Explanation**
```json
{
  "parlay_id": "sgp_abc123",
  "overall_confidence": 0.78,
  "factors": [
    {"name": "Opponent Pass Defense DVOA", "impact": -0.15, "direction": "negative", "detail": "SEA ranked #1"},
    {"name": "Weather: Wind", "impact": -0.05, "direction": "negative", "detail": "12 mph crosswind"},
    {"name": "Sharp Money", "impact": +0.08, "direction": "positive", "detail": "Steam detected on Under"}
  ],
  "leg_explanations": [
    {"leg_index": 0, "text": "Seattle's #1 pass defense historically reduces opponent QB yards by 15%"}
  ]
}
```

---

## 4. Feature Engineering Pipeline

### 4.1 Weather Quantization

```python
def quantize_weather(weather: dict) -> dict:
    wind = weather["wind_mph"]
    
    # Non-linear wind penalty (threshold at 12mph)
    if wind < 12:
        wind_penalty = 0
    elif wind < 18:
        wind_penalty = (wind - 12) * 0.02  # 2% per mph above 12
    else:
        wind_penalty = 0.12 + (wind - 18) * 0.03  # Accelerated decay
    
    return {
        "pass_yards_multiplier": 1 - wind_penalty,
        "fg_accuracy_penalty": wind_penalty * 0.8,
        "run_boost": wind_penalty * 0.5  # Teams run more in wind
    }
```

### 4.2 Injury Impact Adjustment

```python
POSITION_WEIGHTS = {
    "QB": 0.35,  # Highest impact
    "WR1": 0.15,
    "RB1": 0.12,
    "TE1": 0.08,
    "OL": 0.05,
}

def adjust_for_injuries(injuries: list, marginals: dict) -> dict:
    for injury in injuries:
        if injury["status"] == "out":
            impact = 1.0
        elif injury["status"] == "doubtful":
            impact = 0.75
        elif injury["status"] == "questionable":
            impact = 0.4
        else:
            impact = 0.1
        
        # Adjust related player marginals
        affected_players = get_correlated_players(injury["player_id"])
        for player_id, correlation in affected_players:
            marginals[player_id]["mean"] *= (1 - impact * correlation)
    
    return marginals
```

### 4.3 Sentiment → Numeric Prior

```python
def sentiment_to_prior(sentiment_score: float, base_prob: float) -> float:
    """
    Bayesian update: shift probability based on expert sentiment.
    sentiment_score: 0-1 (0.5 = neutral)
    """
    # Limit sentiment influence to ±10% of base probability
    max_shift = 0.10
    shift = (sentiment_score - 0.5) * 2 * max_shift
    
    return np.clip(base_prob + shift, 0.01, 0.99)
```

### 4.4 Steam Detection Logic

```python
def detect_steam(odds_history: list, window_sec: int = 60) -> Optional[dict]:
    """
    Steam = synchronized movement across 3+ books within 60 seconds
    """
    recent = [o for o in odds_history if o["timestamp"] > now() - window_sec]
    
    if len(recent) < 3:
        return None
    
    movements = [o["new_odds"] - o["old_odds"] for o in recent]
    avg_movement = np.mean(movements)
    
    if abs(avg_movement) > 5 and len(set(o["book"] for o in recent)) >= 3:
        return {
            "direction": "away" if avg_movement > 0 else "home",
            "magnitude": abs(avg_movement),
            "book_count": len(set(o["book"] for o in recent))
        }
    return None
```

### 4.5 Entity Resolution (Fuzzy Matching)

```python
from thefuzz import fuzz
from typing import Optional

def resolve_player(external_name: str, source: str, threshold: int = 85) -> Optional[str]:
    """
    Map external player name to internal master_player_id.
    Uses fuzzy matching with manual review queue for low-confidence matches.
    """
    # Check exact match cache first
    cache_key = f"player_map:{source}:{external_name.lower()}"
    cached = redis.get(cache_key)
    if cached:
        return cached["internal_id"]
    
    # Fuzzy match against canonical names
    candidates = db.query("SELECT internal_id, canonical_name FROM player_mappings")
    
    best_match = None
    best_score = 0
    for candidate in candidates:
        score = fuzz.token_sort_ratio(external_name, candidate["canonical_name"])
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_score >= threshold:
        # Cache and return
        redis.setex(cache_key, 86400, {"internal_id": best_match["internal_id"], "confidence": best_score/100})
        return best_match["internal_id"]
    elif best_score >= 70:
        # Flag for manual review
        db.execute("UPDATE player_mappings SET needs_review = TRUE WHERE internal_id = %s", best_match["internal_id"])
        return best_match["internal_id"]  # Best guess
    
    return None  # Unresolvable
```

### 4.6 Geofencing (State-Based Book Visibility)

```python
import geoip2.database

STATE_BOOK_MATRIX = {
    "NY": ["draftkings", "fanduel", "caesars", "betmgm"],
    "NJ": ["draftkings", "fanduel", "caesars", "betmgm", "pointsbet"],
    "PA": ["draftkings", "fanduel", "betmgm"],
    "CA": [],  # No sports betting - show DFS only
    "UT": [],  # No gambling at all
    # ... full state matrix
}

DFS_FALLBACK = ["prizepicks", "underdog"]  # For states without sports betting

def get_allowed_books(ip_address: str) -> dict:
    """
    Returns sportsbooks available to user based on geolocation.
    Critical for Apple App Store compliance.
    """
    # Check cache first
    ip_hash = hashlib.md5(ip_address.encode()).hexdigest()
    cached = redis.get(f"geo:{ip_hash}")
    if cached:
        return cached
    
    # MaxMind GeoIP2 lookup
    reader = geoip2.database.Reader('/path/to/GeoLite2-City.mmdb')
    response = reader.city(ip_address)
    state = response.subdivisions.most_specific.iso_code
    
    allowed = STATE_BOOK_MATRIX.get(state, [])
    result = {
        "state": state,
        "allowed_books": allowed if allowed else DFS_FALLBACK,
        "is_dfs_only": len(allowed) == 0
    }
    
    redis.setex(f"geo:{ip_hash}", 3600, result)
    return result
```

---

## 5. Explainable AI Layer

### 5.1 SHAP Approximation Strategy

Full SHAP is computationally expensive (~40ms/leg). We use a **hybrid approach**:

| Factor Type | Method | Compute Time |
|-------------|--------|--------------|
| Static (DVOA, historical) | Precomputed lookup table | <1ms |
| Dynamic (weather, injuries) | Linear feature attribution | <5ms |
| Correlation effects | Marginal contribution sampling | <20ms |

### 5.2 Precomputed vs On-Demand

```
PRECOMPUTED (Nightly Batch):
├── Team defensive impact tables
├── Player historical performance distributions
├── Venue effect modifiers
└── Head-to-head historical correlations

ON-DEMAND (Per Request):
├── Weather impact calculation
├── Injury status adjustments
├── Live odds movement analysis
└── Correlation-conditioned probability shifts
```

### 5.3 Uncertainty Communication

```javascript
// Frontend component
<ConfidenceGauge 
  probability={0.29}
  confidenceInterval={[0.24, 0.34]}
  sampleSize={10000}
  modelAgreement={0.85}  // % of sub-models agreeing
/>

// Visual: Bell curve with shaded confidence region
// Text: "Our model estimates 29% probability (range: 24-34%)"
```

### 5.4 JAX Student-t Copula Kernel (Tail Dependence)

> [!CAUTION]
> **Critical Change**: Gaussian Copula underestimates "blowout" correlations. Student-t captures tail dependence via ν.

```python
import jax
import jax.numpy as jnp

@jax.jit
def simulate_parlay_t_copula(
    cholesky_matrix: jnp.ndarray,  # Cholesky of correlation matrix
    means: jnp.ndarray,            # Marginal means
    thresholds: jnp.ndarray,       # Z-score thresholds for legs
    nu: float = 5.0,               # Degrees of freedom (lower = fatter tails)
    n_sims: int = 10000,
    key: int = 0
) -> dict:
    """
    Student-t Copula: Superior for sports because it captures
    'tail dependence' (OT games push ALL overs together).
    """
    rng_key = jax.random.PRNGKey(key)
    k1, k2 = jax.random.split(rng_key)

    # 1. Generate Multivariate Normal samples
    z_norm = jax.random.normal(k1, shape=(n_sims, len(means)))
    
    # 2. Correlate them
    z_corr = jnp.dot(z_norm, cholesky_matrix.T)
    
    # 3. Generate Chi-Squared for heavy tails
    w = jax.random.chisquare(k2, df=nu, shape=(n_sims, 1)) / nu
    
    # 4. Convert to Student-t variates: t = Z / sqrt(W)
    t_samples = z_corr / jnp.sqrt(w) + means
    
    # 5. Check wins
    wins = t_samples > thresholds
    parlay_hits = jnp.all(wins, axis=1)
    prob_parlay = jnp.mean(parlay_hits)
    
    # 6. Correlation edge vs independence
    marginal_probs = jnp.mean(wins, axis=0)
    prob_independent = jnp.prod(marginal_probs)

    return {
        "true_probability": prob_parlay,
        "correlation_multiplier": prob_parlay / prob_independent,
        "tail_risk_factor": 1.0 / nu
    }

# Warmup: ~2s on first call, <50ms GPU / <150ms CPU thereafter
```

### 5.5 Regime Detection (Game Script Classifier)

```python
from enum import Enum

class GameRegime(Enum):
    BLOWOUT = "blowout"      # One team dominates, garbage time stats
    SHOOTOUT = "shootout"    # High-scoring, passing heavy
    DEFENSIVE = "defensive"  # Low-scoring, run heavy
    NORMAL = "normal"        # Standard game script

def detect_regime(matchup: dict) -> tuple[GameRegime, float]:
    """
    Classify expected game script and return optimal ν parameter.
    Lower ν = fatter tails = more tail correlation.
    """
    spread = abs(matchup["spread"])
    total = matchup["total"]
    home_off_dvoa = matchup["home_off_dvoa"]
    away_def_dvoa = matchup["away_def_dvoa"]
    
    # Blowout: Large spread + mismatch
    if spread >= 10:
        return GameRegime.BLOWOUT, 3.0  # Heavy tails (garbage time)
    
    # Shootout: High total + good offenses
    if total >= 52 and home_off_dvoa > 0.1:
        return GameRegime.SHOOTOUT, 4.0  # Moderate tails
    
    # Defensive: Low total + good defenses
    if total <= 40 and away_def_dvoa < -0.1:
        return GameRegime.DEFENSIVE, 6.0  # Lighter tails
    
    return GameRegime.NORMAL, 5.0  # Default
```

---

## 6. API Design

### 6.1 Public API (Frontend → Backend)

```yaml
POST /api/v1/parlays/generate
  Auth: Bearer JWT
  Rate Limit: 60/min (free), 300/min (pro)
  Body: { game_id, legs[], context? }
  Response: { parlay, explanation, slipbuilder_data }

GET /api/v1/games/{game_id}/odds
  Response: { odds_by_book[], best_lines[], steam_alerts[] }

GET /api/v1/players/{player_id}/projections
  Response: { marginals, historical_stats, injury_status }

POST /api/v1/parlays/{parlay_id}/slipbuilder
  Body: { sportsbook: "draftkings" | "fanduel" | ... }
  Response: { 
    clipboard_text: "Stafford Over 265.5 Pass Yds, Kupp Anytime TD",
    game_page_deeplink: "draftkings://sportsbook/game/nfl_sea_lar",
    instructions: "Picks copied! Tap to open DraftKings and add legs manually."
  }

GET /api/v1/user/history
  Response: { parlays[], win_rate, roi, clv_avg }
```

### 6.1.1 SlipBuilder: Why Not Direct SGP Deep Links?

> [!WARNING]
> **Technical Reality**: SGP deep-linking is **impossible** without enterprise partnerships. FanDuel/DraftKings SGP URLs are hashed and encrypted.

**The SlipBuilder Flow:**
1. User clicks "Bet on FanDuel"
2. App copies leg details to clipboard ("Stafford O265.5, Kupp TD")
3. App opens FanDuel to the GAME PAGE (not slip - that's encrypted)
4. Toast: "Picks copied! Add them to your Same Game Parlay"

**Frontend Implementation:**
```typescript
async function handleBetClick(parlay: Parlay, book: string) {
  const response = await api.post(`/parlays/${parlay.id}/slipbuilder`, { sportsbook: book });
  await navigator.clipboard.writeText(response.clipboard_text);
  showToast("Picks copied! Add them to your SGP.", { duration: 5000 });
  window.location.href = response.game_page_deeplink;
}
```

### 6.2 Internal Service APIs

```yaml
# Copula Engine (gRPC for performance)
rpc Simulate(SimulationRequest) returns (SimulationResult)
rpc GetMarginals(PlayerStatRequest) returns (Marginals)
rpc UpdateCorrelationMatrix(LeagueSeasonRequest) returns (Status)

# Feature Pipeline
POST /internal/features/weather
POST /internal/features/injuries
POST /internal/features/sentiment
```

### 6.3 Failure Modes

| Failure | Detection | Fallback |
|---------|-----------|----------|
| Odds feed stale (>30s) | Heartbeat monitoring | Show "stale" badge, use cached |
| Simulation timeout | 500ms deadline | Return cached similar parlay |
| Weather API down | HTTP 5xx | Use venue-based historical avg |
| Sportsbook API 429 | Rate limit headers | Exponential backoff |

---

## 7. MVP → V1 → V2 Roadmap

### MVP (Weeks 1-12)

**Scope:**
- Single sport: NFL only
- 3 sportsbooks: DraftKings, FanDuel, BetMGM
- Polling-based odds (5s interval) — not WebSocket
- Pre-built correlation matrices (static, no real-time updates)
- 2-3 leg parlays only
- Basic XAI (text explanations, no SHAP visualization)
- Web only (Next.js)

**What NOT to build:**
- Mobile app
- Real-time simulation updates
- Custom user bankroll management
- Multi-sport support
- Revenue share tracking

**Tech Stack:**
- Frontend: Next.js + Vercel
- Backend: Single Python FastAPI monolith
- Database: Supabase (Postgres)
- Cache: Upstash Redis
- Queue: None (synchronous)

---

### V1 (Weeks 13-24)

**Additions:**
- WebSocket odds ingestion (Redpanda)
- NBA support
- Dynamic correlation matrix updates (triggered by significant events)
- 4-5 leg parlays
- Full SHAP visualization
- React Native mobile app (iOS) — categorize as "Sports Analysis / Utility" NOT "Gambling"
- Steam alerts (push notifications)
- Pro subscription tier ($29.99/mo)
- **Geofencing integration** (MaxMind) for state-based book visibility
- **Entity Resolution service** with manual review queue

**Architecture Evolution:**
- Break monolith into: Parlay Service, Odds Service, Copula Engine
- Add Kubernetes for orchestration
- Implement proper observability (Datadog/Grafana)

---

### V2 / Moat Phase (Weeks 25-52)

**Competitive Advantages:**
- Proprietary correlation matrices trained on 5+ years of data
- Real-time sentiment pipeline (Twitter API, beat writer feeds)
- Personalized recommendations (user betting history ML)
- Live in-game SGP optimization
- Enterprise API for smaller affiliates
- Android app
- Conversational AI interface (LLM + function calling)

**Defensibility:**
- Data moat: Historical simulation results create feedback loop
- Network effects: More users → more bet outcome data → better models
- Integration depth: QuickSlip partnerships with all major books
- **CLV tracking**: Prove model value with Closing Line Value metrics

---

## 7.1 Monetization Strategy (CPA-First)

> [!WARNING]
> **Sharp Traffic Risk**: If your app works and users win, RevShare goes negative. Sportsbooks will actively terminate affiliates sending winning traffic.

**Strategy:**

| Phase | Model | Rationale |
|-------|-------|----------|
| MVP-V1 | **CPA Only** | $150-300 per depositing user. Revenue protected from user wins. |
| V2+ | Hybrid (CPA + capped RevShare) | Negotiate cap on negative carryover after proving traffic quality |

**CPA Rates (2026):**
- DraftKings: $200-300 CPA
- FanDuel: $200-275 CPA  
- BetMGM: $150-250 CPA
- Caesars: $175-275 CPA

**Subscription Revenue:**
- Free Tier: 3 AI picks/week, basic odds comparison
- Pro Tier ($29.99/mo): Unlimited SGPs, full XAI, steam alerts
- Enterprise API: $2,500/mo for data access

---

## 8. Legal & Compliance by Design

### 8.1 Avoiding Sportsbook Classification

> [!CAUTION]
> The system MUST NOT accept wagers, hold funds, or determine bet outcomes.

**Architectural Safeguards:**
- No wallet/payment system in codebase
- All "Place Bet" actions redirect to licensed sportsbooks
- No odds offered by the platform itself
- Clear affiliate disclosure on every recommendation

### 8.2 Affiliate Compliance

| State | Requirement | Implementation |
|-------|-------------|----------------|
| NJ | Vendor Registration | File with DGE, display registration # |
| CO | Sports Betting Vendor License | $350 filing, annual renewal |
| MI | Background check for RevShare | **CPA-only model avoids this** |

### 8.2.1 Apple App Store Compliance

> [!IMPORTANT]
> Categorize as **"Sports Analysis / Utility"**, NOT "Gambling". Do NOT process payments for bets.

**Requirements:**
- Implement geofencing to hide deep-links in prohibited states
- No broken links (if user clicks "Bet on DraftKings" in Utah, show graceful fallback)
- Include responsible gaming resources
- Age verification gate

### 8.3 Disclaimers

```javascript
// Displayed on every parlay recommendation
const LEGAL_DISCLAIMER = `
For entertainment purposes only. Gambling involves risk. 
Past performance does not guarantee future results.
Must be 21+. If you or someone you know has a gambling problem,
call 1-800-GAMBLER.
`;
```

### 8.4 Responsible Gaming Features

- Self-exclusion link in user settings
- "Cooling off" period option (block app for X days)
- Daily/weekly loss tracking
- 1-800-GAMBLER displayed prominently

### 8.5 SAFE Bet Act Considerations

**What NOT to do:**
- Track individual user betting patterns for "nudges"
- Personalize based on loss-chasing behavior
- Send push notifications after losses

**Safe practices:**
- Focus on market analysis, not user exploitation
- Log betting preferences, not outcomes
- No A/B testing on addiction-related features

---

## 9. Engineering Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Data Latency** — Odds arrive late, +EV window closes | High | High | Invest in WebSocket infrastructure early; alert users when data is stale |
| **Model Drift** — Correlations change mid-season | Medium | High | Weekly automated backtests; alert on prediction accuracy drop >5% |
| **Legal Risk** — State changes affiliate rules | Medium | Critical | Stay CPA-only initially; monitor regulatory updates; retain gaming attorney |
| **Infra Cost Explosion** — Simulation costs scale | Medium | Medium | Cache popular parlays; batch similar requests; GPU spot instances |
| **User Trust Failure** — Losing streak → churn | High | High | Emphasize long-term EV; show historical accuracy; never overpromise |
| **Sportsbook API Changes** — Deep links break | Medium | Medium | Abstract affiliate layer; monitor for changes; backup manual instructions |
| **Competition** — Major player copies model | Low | Medium | Focus on data moat and UX; speed to market matters |

---

## 10. Strategic Summary

### The System's Moat

This platform's defensibility stems from **data compounding**. Every simulation generates signals about correlation accuracy. Every user bet outcome feeds back into model refinement. After 6-12 months, the proprietary correlation matrices—trained on millions of simulated scenarios validated against real outcomes—become impossible to replicate without the same operational history. Combined with first-mover QuickSlip integrations and brand trust, this creates a sustainable competitive advantage.

### Why Sportsbooks Can't Easily Copy This

Sportsbooks are optimized for volume and margin, not user education. Their incentive is to keep the bettor uninformed. Building a transparent, explainable recommendation engine cannibalizes their existing SGP margins. Culturally, books are risk-management operations, not consumer fintech products. The organizational DNA required to build and iterate on an XAI-powered betting assistant simply doesn't exist within their compliance-heavy, profit-margin-focused structures.

### Why Users Will Trust This Over Twitter Picks

Twitter handicappers operate on survivorship bias—only winners post screenshots. This system offers mathematical transparency: users see the correlation logic, the probability distributions, and the confidence intervals. When a bet loses, the user understands *why* the model was wrong, not just that some anonymous tout was wrong. Over time, verifiable expected value (tracked, timestamped, backtested) will outperform "trust me bro" credibility every time.

---

## Verification Plan

### Automated Tests

Since this is a greenfield project, verification will focus on:

1. **Unit Tests**: Each service will have pytest test suites
2. **Integration Tests**: Docker Compose environment simulating full data flow
3. **Backtest Framework**: Historical odds data replayed to validate +EV predictions
4. **CLV Tracking**: Monitor if recommended lines get worse (proves model accuracy)

### Manual Verification

After MVP build:
1. Place 50 paper bets based on system recommendations
2. Track outcomes over 2-week period
3. Calculate actual ROI vs predicted EV
4. User acceptance testing with 5 beta testers

---

> [!IMPORTANT]
> **Next Steps**: Upon approval, I will begin setting up the project structure with the core Python Copula engine and FastAPI backend.
