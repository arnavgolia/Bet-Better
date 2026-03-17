# SmartParlay Auto-Builder - Executive Summary

**Status**: 📋 Planning Complete - Awaiting Approval to Implement
**Date**: February 1, 2026

---

## 🎯 What You Asked For

You wanted:
1. **Fix missing TD props** and all other FanDuel prop types
2. **Build the core feature**: Natural language auto-parlay construction
   - "Build me a 5-leg parlay for the Super Bowl"
   - "Give me a super safe money bet"
   - "Make me a high-risk cross-game parlay"

---

## ✅ What I've Done (Planning Phase)

I've created a **complete architectural design** for the auto-parlay intelligence system. This is NOT code yet - it's a comprehensive blueprint that covers:

### 📄 Documents Created:

1. **`AUTO_PARLAY_ARCHITECTURE.md`** (50+ pages)
   - Complete system design from input to output
   - All algorithms and logic explained
   - Database schema changes
   - API endpoints
   - UI flows
   - Edge case handling

2. **`IMPROVEMENT_PLAN.md`** (from earlier)
   - Identified the TD Scorer issue
   - UI improvement plan

3. **`UI_IMPROVEMENTS_SUMMARY.md`** (from earlier)
   - FanDuel-style redesign (already completed)

---

## 🏗️ System Overview

### The Problem We're Solving

**Current State**:
- User manually selects each prop one-by-one
- No guidance on which props work well together
- No understanding of correlation or risk
- Missing most FanDuel prop types (TDs, alt lines, game lines, etc.)

**Desired State**:
- User types what they want: "Build me a safe 5-leg Super Bowl parlay"
- System auto-constructs the optimal parlay
- Explains why each leg was chosen
- Offers safer/riskier alternatives
- Handles all prop types FanDuel has

### The Solution Architecture

```
User Input: "Build me a 5-leg parlay for the Super Bowl"
     ↓
Intent Parser: Extracts legs=5, event=Super Bowl, risk=balanced
     ↓
Candidate Generator: Finds 247 available props
     ↓
Compatibility Filter: Removes conflicting combinations
     ↓
Parlay Optimizer: Scores all valid combos, picks best
     ↓
Copula Analysis: Validates correlation and EV
     ↓
Response Generator: Explains each leg + alternatives
     ↓
User sees beautiful parlay with "Why?" for each leg
```

---

## 🔑 Key Design Decisions

### 1. Prop Coverage (FanDuel Parity)

**Added 40+ New Prop Types**:
- **Scoring**: First TD, Last TD, 2+ TDs, Anytime TD
- **Alt Lines**: Alt Receiving, Alt Rushing, Alt Passing
- **Game Lines**: Spread, Alt Spread, Totals, Alt Totals, Moneyline
- **Special**: Longest Reception, Longest Rush, Sacks, etc.

**Database Changes**:
- New `alt_lines` table for alternative lines
- New `game_props` table for spread/total/ML
- Extended `player_marginals` with metadata (sharp%, public%, line movement)

### 2. Natural Language Processing

**Intent Detection**:
- Parses user requests into structured constraints
- Detects: leg count, risk profile, sport, games, prop preferences
- Handles variations: "5-leg", "five leg", "5 pick", etc.

**Examples**:
```
Input: "Build me a safe 5-leg Super Bowl parlay"
Output: {
  legs: 5,
  risk_profile: "safe",
  games: [{ type: "championship", sport: "NFL" }],
  correlation_strategy: "positive_correlation"
}

Input: "Make me a degen 8-leg cross-game NFL parlay with only passing"
Output: {
  legs: 8,
  risk_profile: "degen",
  sports: ["NFL"],
  allowed_props: ["passing"],
  correlation_strategy: "minimize_correlation"
}
```

### 3. Risk Profiles

**Four Distinct Strategies**:

| Profile | Win % Target | Odds Range | Strategy |
|---------|-------------|------------|----------|
| **Safe** | 35%+ | -200 to +400 | High confidence, positive correlation |
| **Balanced** | 25%+ | +200 to +1000 | Mix of value and safety |
| **Aggressive** | 15%+ | +800 to +5000 | High EV, independent legs |
| **Degen** | 5%+ | +2000 to +50000 | Maximum upside, lottery ticket |

Each profile has custom:
- Scoring weights (EV vs confidence vs variance)
- Prop type preferences
- Correlation strategies
- Target odds ranges

### 4. Correlation & Compatibility Rules

**Smart Leg Pairing**:
- ✅ Positive: QB Pass Yards + WR Rec Yards (same team)
- ✅ Positive: RB Rush Yards + Team Spread Cover
- ⚠️ Negative: QB Pass Yards + Opponent Blowout
- ⛔ Forbidden: Same prop, opposite directions

**Historical Data**:
- Tracks actual correlation from thousands of games
- Example: "Passing Yards Over" + "Receiving Yards Over" = +0.72 correlation

### 5. Multi-Dimensional Scoring

**Every parlay is scored on**:
- Expected Value (dollars per $100 bet)
- Win Probability (copula-adjusted)
- Variance (risk measure)
- Correlation (independence factor)
- Confidence (model certainty)
- Sharp Money % (professional action)
- Weather Impact
- Injury Impact
- Matchup Rating

**Result**: Best possible parlay for each risk profile

### 6. Explainability

**Every leg comes with**:
- **Primary Reason**: "Mahomes averages 312 yards vs zone coverage, Eagles run 68% zone"
- **Supporting Factors**: ["Hot streak: 340 yds in last 5 games", "Sharp money 73%"]
- **Historical Context**: "82% hit rate in playoffs"
- **Matchup Analysis**: "Eagles rank 28th vs QB passing"
- **Correlation Note**: "Positively correlated with Kelce receptions (0.65)"

**Transparency = Trust**

### 7. Alternatives System

**Every parlay comes with 3 alternatives**:
1. **Safer Version**: Lower odds, higher win probability
2. **Riskier Version**: Higher payout, more variance
3. **Same-Game Version**: All legs from one game (SGP)

User can swap instantly.

---

## 🛡️ Edge Cases Covered

1. **Missing Props**: Graceful degradation, suggests alternatives
2. **Odds Movement**: Monitors in real-time, warns user
3. **Injuries**: Auto-detects, rebuilds parlay if player ruled out
4. **Props Removed**: Validates before user places bet
5. **State Restrictions**: Filters props based on user location (NY, IL, LA rules)
6. **Insufficient Data**: Reduces legs or expands game selection
7. **Market Closed**: Checks game hasn't started

---

## 📅 Implementation Roadmap

### 14-Week Plan (3.5 Months)

**Phase 1-2 (Weeks 1-3)**: Foundation + Intent Parser
- Add all missing prop types to backend
- Ingest full FanDuel data
- Build NLP intent parser
- **Deliverable**: Can parse user requests into constraints

**Phase 3-4 (Weeks 4-6)**: Candidate Generation + Compatibility
- Build candidate filtering
- Create correlation matrix
- Implement compatibility rules
- **Deliverable**: Can filter valid prop combinations

**Phase 5-6 (Weeks 7-10)**: Scoring + UX
- Build multi-dimensional scorer
- Create optimizer
- Design beautiful UI
- Add explanations
- **Deliverable**: Working auto-builder with explanations

**Phase 7-8 (Weeks 11-14)**: Edge Cases + Production
- Handle all failures
- Add monitoring
- Load testing
- **Deliverable**: Production-ready system

---

## 💰 Value Proposition

### Why This Feature Wins

1. **Removes Friction**: No more manual prop selection
2. **Educates Users**: Explains *why* each leg makes sense
3. **Builds Trust**: Transparent reasoning, not black box
4. **Matches User Intent**: Safe vs risky vs YOLO
5. **Differentiation**: No other parlay tool does this well

### Target User Stories

**Casual Bettor** (Sarah):
- "I want a Super Bowl parlay but don't know which props to pick"
- SmartParlay: Builds safe 5-leg parlay with clear explanations
- Outcome: She understands and trusts the bet

**Sharp Bettor** (Mike):
- "I want a high-EV cross-game parlay following sharp money"
- SmartParlay: Finds +EV legs with 70%+ sharp backing
- Outcome: He gets edges he'd spend hours finding manually

**YOLO Bettor** (Jake):
- "Give me a lottery ticket for $10 to win $5,000"
- SmartParlay: Builds 10-leg moonshot with low correlation
- Outcome: Max entertainment value

---

## 🚨 Critical Dependencies

To implement this, we need:

1. **Backend Work**:
   - Extend PropType enum with 40+ new types
   - Create alt_lines and game_props tables
   - Update ingestion scripts for full FanDuel coverage
   - Add metadata fields (sharp%, public%, line movement)

2. **ML Work**:
   - Integrate intent parser with copula analysis
   - Compute historical correlation matrix
   - Build multi-dimensional scoring

3. **Frontend Work**:
   - Create auto-builder UI
   - Build explanation components
   - Add alternative cards
   - FanDuel deep linking

4. **Data Work**:
   - Scrape full FanDuel prop catalog
   - Track line movements
   - Monitor sharp money indicators

---

## 📊 Success Metrics

**How We'll Know It's Working**:

1. **Adoption**: 60%+ of users try auto-builder within first session
2. **Satisfaction**: 4+ star rating on auto-built parlays
3. **Conversion**: 40%+ of auto-built parlays actually placed
4. **Retention**: Users return to auto-builder for future bets
5. **Trust**: Low modification rate (users accept suggestions)

---

## ❓ Questions for You

Before I start implementing:

1. **Timeline**: Is 14 weeks acceptable? Can we do phased rollout?
2. **Priorities**: Should I focus on certain sports first (NFL only)?
3. **Data Access**: Do we have FanDuel API access or need to scrape?
4. **Infrastructure**: Any backend constraints I should know about?
5. **User Testing**: Can we beta test with small group first?

---

## 📝 Next Steps

**If you approve this plan**:

1. I'll start with **Phase 1** (prop coverage foundation)
2. We can iterate on each phase with your feedback
3. I'll provide weekly progress updates
4. We can adjust timeline/scope as needed

**If you want changes**:

1. Tell me what to adjust in the plan
2. I'll revise and re-submit
3. We can discuss trade-offs and priorities

---

## 🎯 The Big Picture

This isn't just adding a feature - it's **transforming SmartParlay from a parlay calculator into an AI betting assistant**.

The auto-builder becomes the core of the product. Everything else (manual prop selection, copula analysis) becomes secondary features for advanced users.

**The pitch becomes**:
> "Tell SmartParlay what you want. It builds the optimal parlay, explains every leg, and gives you alternatives. Backed by statistical modeling and real-time data."

This is the feature that gets people to switch from FanDuel's basic parlay builder to SmartParlay.

---

## 📄 Review Materials

**Full Technical Spec**: `/AUTO_PARLAY_ARCHITECTURE.md` (50 pages)
- Every algorithm explained
- All database schemas
- Complete UX flows
- Edge case handling
- Code examples (pseudocode)

**Read this if you want to understand**:
- Exactly how intent parsing works
- How correlation scoring is calculated
- How risk profiles differ
- What the UI will look like
- How we handle failures

---

## ✅ Your Decision

Please review the architecture document and let me know:

1. ✅ **Approved** - Start Phase 1 implementation
2. 🔄 **Needs Changes** - Specific feedback on what to adjust
3. ❓ **Questions** - Want to discuss certain aspects first

I'm ready to start building as soon as you give the green light!

---

**Remember**: This planning document is the result of thinking through ALL the implications, edge cases, and design decisions BEFORE writing code. It's the "measure twice, cut once" approach you asked for.

The implementation will be much faster and higher quality because we've done the hard thinking upfront.
