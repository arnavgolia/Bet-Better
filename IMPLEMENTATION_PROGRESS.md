# Auto-Parlay Implementation Progress

**Started**: February 1, 2026
**Status**: Phase 1 In Progress (Foundation)

---

## ✅ Completed So Far

### 1. Backend Schema Extensions

#### PropType Enum Extended (40+ New Types)
**File**: `backend/app/models/schemas/parlay.py`

Added comprehensive prop type coverage:
- **Passing**: Alt Passing Yards, Alt TDs, Longest Completion, Sacks Taken
- **Rushing**: Alt Rushing Yards, Rush TDs, Longest Rush, Rush Attempts
- **Receiving**: Alt Receiving Yards, Receiving TDs, Alt Receptions, Longest Reception
- **Scoring**: First TD, Last TD, 2+ TDs, 3+ TDs
- **Game Props**: Spread, Alt Spread, Total, Alt Total, Moneyline, Half-time lines
- **Special**: Winning Margin, First Score, Field Goals, etc.

**Result**: Full FanDuel parity for prop types ✅

---

### 2. Database Migrations Created

#### New Migration File
**File**: `backend/migrations/versions/add_auto_parlay_tables.py`

**New Tables**:
1. **`alt_lines`** - Alternative lines for props (e.g., 50.5, 55.5, 60.5 for same player)
2. **`game_props`** - Game-level props (spreads, totals, moneylines)
3. **`prop_metadata`** - Historical data, matchup info, projections
4. **`auto_parlay_requests`** - User requests and parsed intents
5. **`built_parlays`** - Auto-generated parlays with scores
6. **`parlay_leg_explanations`** - Reasoning for each leg selection

**Extended Tables**:
- **`player_marginals`** - Added: prop_category, sharp_percentage, public_percentage, line_opened, line_current, steam_move, historical_hit_rate

**Status**: Ready to migrate ⏳ (needs `alembic upgrade head`)

---

### 3. Ingestion Scripts Updated

#### Enhanced Player Props Ingestion
**File**: `backend/scripts/ingest_fanduel_data.py`

**Updates**:
- Expanded `PROP_MARKETS` from 5 to 22 markets
- Updated `STAT_MAP` to cover all new prop types
- Now ingests: passing, rushing, receiving, TDs, kicking props

**New Markets**:
```python
PROP_MARKETS = [
    "player_pass_yds", "player_pass_tds", "player_pass_completions",
    "player_rush_yds", "player_rush_tds", "player_rush_longest",
    "player_reception_yds", "player_receptions", "player_reception_longest",
    "player_anytime_td", "player_1st_td", "player_last_td",
    "player_2+_tds", "player_field_goals", # ... and more
]
```

#### New Game Props Ingestion Script
**File**: `backend/scripts/ingest_game_props.py`

**Purpose**: Fetch spreads, totals, and moneylines from The Odds API

**Features**:
- Fetches FanDuel game lines
- Stores spread, total, moneyline for each game
- Updates game table with quick-reference lines

**Status**: Created, ready to test ✅

---

### 4. Intent Parser System

#### Natural Language → Structured Constraints
**File**: `backend/app/services/auto_parlay/intent_parser.py`

**Capabilities**:
- Parses user requests like "Build me a 5-leg Super Bowl parlay"
- Extracts: leg count, risk profile, sports, games, prop preferences
- Detects: correlation strategy, odds targets, special events
- Handles: "safe", "aggressive", "degen", cross-game, cross-sport

**Risk Profiles**:
- Safe: Conservative, high-confidence picks
- Balanced: Mix of value and safety
- Aggressive: High-risk, high-reward
- Degen: Lottery ticket, maximum variance

**Example Output**:
```python
Input: "Give me a super safe 5-leg Super Bowl parlay"
Output: UserIntent(
    num_legs=5,
    risk_profile=RiskProfile.SAFE,
    sports=['NFL'],
    games=[GameSelector(type='championship', sport='NFL')],
    correlation_strategy=CorrelationStrategy.POSITIVE_CORRELATION
)
```

**Status**: Core implementation complete ✅

---

## 📋 Current Phase: Phase 1 - Foundation

### Phase 1 Goals (Week 1-2)
- [x] Extend PropType enum with all missing types
- [x] Create alt_lines table
- [x] Create game_props table
- [x] Create prop_metadata table
- [x] Create auto_parlay tables
- [x] Write ingest_game_props.py script
- [x] Update ingest_fanduel_data.py with new STAT_MAP
- [x] Build Intent Parser
- [ ] Run database migrations
- [ ] Test ingestion on live data
- [ ] Verify all prop types appear in database

### What's Next (Immediate)
1. Run `alembic upgrade head` to apply migrations
2. Test `ingest_game_props.py` on live NFL data
3. Test `ingest_fanduel_data.py` with expanded markets
4. Verify database has full prop coverage

---

## 🚧 Upcoming Phases

### Phase 2: Candidate Generation (Week 3-4)
**Next To Build**:
- [ ] Candidate Generator class
- [ ] SQL query builder for filtering props
- [ ] Weather adjustment logic
- [ ] Sharp money filter
- [ ] Injury filter

### Phase 3: Correlation & Compatibility (Week 5-6)
**Next To Build**:
- [ ] Prop relationships matrix
- [ ] Compatibility Engine
- [ ] Correlation Engine
- [ ] Historical correlation data

### Phase 4: Scoring & Optimization (Week 7-8)
**Next To Build**:
- [ ] Comprehensive Scorer
- [ ] Parlay Optimizer
- [ ] Alternative generator
- [ ] Integration with copula analysis

### Phase 5: UX & API (Week 9-10)
**Next To Build**:
- [ ] Auto-parlay API endpoint
- [ ] Frontend UI components
- [ ] Explanation generator
- [ ] FanDuel deep links

---

## 📊 Files Created/Modified

### Created (New Files)
1. `backend/migrations/versions/add_auto_parlay_tables.py`
2. `backend/scripts/ingest_game_props.py`
3. `backend/app/services/auto_parlay/intent_parser.py`
4. `AUTO_PARLAY_ARCHITECTURE.md` (50+ page spec)
5. `EXECUTIVE_SUMMARY.md` (high-level overview)
6. `IMPLEMENTATION_PROGRESS.md` (this file)

### Modified (Updated Files)
1. `backend/app/models/schemas/parlay.py` - Extended PropType enum
2. `backend/scripts/ingest_fanduel_data.py` - Expanded PROP_MARKETS and STAT_MAP

---

## 🎯 Deliverables Status

| Component | Status | Notes |
|-----------|--------|-------|
| Database Schema | ✅ Complete | Migration file created |
| PropType Enum | ✅ Complete | 40+ prop types added |
| Ingestion Scripts | ✅ Complete | Player & game props |
| Intent Parser | ✅ Complete | NLP to constraints |
| Database Migration | ⏳ Pending | Need to run `alembic upgrade` |
| Test Ingestion | ⏳ Pending | Waiting for migration |
| Candidate Generator | 🔜 Next | Phase 2 |
| Correlation Engine | 🔜 Later | Phase 3 |
| Parlay Optimizer | 🔜 Later | Phase 4 |
| Frontend UI | 🔜 Later | Phase 5 |

---

## 🧪 Testing Plan

### Phase 1 Testing (Next Steps)
1. **Database Migration**:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Test Game Props Ingestion**:
   ```bash
   python -m scripts.ingest_game_props
   ```
   - Verify spreads, totals, moneylines are stored
   - Check FanDuel data is accurate

3. **Test Player Props Ingestion**:
   ```bash
   python -m scripts.ingest_fanduel_data
   ```
   - Verify new prop types (TDs, alt lines, etc.)
   - Check expanded STAT_MAP works
   - Confirm 200+ props for Super Bowl

4. **Test Intent Parser**:
   ```bash
   python -m app.services.auto_parlay.intent_parser
   ```
   - Run test cases
   - Verify parsing accuracy

---

## 📈 Progress Metrics

**Completion by Phase**:
- Phase 1 (Foundation): **~75% Complete**
  - Schema: 100% ✅
  - Ingestion: 100% ✅
  - Intent Parser: 100% ✅
  - Testing: 0% ⏳

**Overall Project**: **~12% Complete** (Phase 1 of 8)

**Estimated Time Remaining**: 13 weeks for full implementation

---

## 🔑 Key Decisions Made

1. **Database Strategy**: Created separate tables for alt_lines and game_props rather than extending player_marginals. This allows cleaner queries and better performance.

2. **Intent Parser**: Built robust NLP system with keyword matching and regex patterns. Can be enhanced later with ML if needed.

3. **Prop Type Granularity**: Separated all prop variants (e.g., passing_yards vs alt_passing_yards vs longest_completion) for precise filtering.

4. **Migration Approach**: Single large migration for all auto-parlay tables to simplify deployment.

---

## ❓ Open Questions

1. **API Rate Limits**: The Odds API has rate limits. Need to implement caching and rate limiting for production.

2. **Alt Lines Discovery**: How do we discover what alternative lines are available? May need to query API differently or scrape FanDuel directly.

3. **Sharp Money Data**: Where do we get sharp percentage vs public percentage? May need third-party service (Action Network, etc.)

4. **Historical Data**: Need to backfill historical player performance. Consider ESPN API or similar.

---

## 💡 Next Session Tasks

When we resume:
1. Run database migrations
2. Test both ingestion scripts
3. Begin building Candidate Generator
4. Create constraint resolution logic
5. Start on prop compatibility rules

---

**Last Updated**: February 1, 2026 7:35 PM
**Progress**: Phase 1 (Foundation) - 75% Complete
