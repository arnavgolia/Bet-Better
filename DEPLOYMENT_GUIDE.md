# Deployment Guide - Bet Better Auto-Parlay System

**Last Updated**: February 1, 2026
**Status**: Ready for Deployment
**Version**: 1.0.0

---

## 🎯 Overview

This guide will walk you through deploying the complete Bet Better system with the new Auto-Parlay AI Builder feature. All code has been implemented and tested - this guide covers the steps to get everything running.

---

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 7.x or higher (optional, for caching)

### Required Tools
```bash
# Check versions
python3 --version  # Should be 3.11+
node --version     # Should be 18+
npm --version
psql --version     # Should be 14+
```

---

## 🗄️ Database Setup

### Step 1: Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE bet_better;

# Create user (if needed)
CREATE USER bet_better_user WITH PASSWORD 'your_secure_password';

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE bet_better TO bet_better_user;

# Exit
\q
```

### Step 2: Configure Environment

```bash
cd backend

# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env
```

**Update these critical values in `.env`:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://bet_better_user:your_secure_password@localhost:5432/bet_better

# API Keys (get from FanDuel, The Odds API, etc.)
FANDUEL_API_KEY=your_fanduel_api_key
ODDS_API_KEY=your_odds_api_key

# Security
SECRET_KEY=your_long_random_secret_key_here
API_VERSION=v1

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Step 3: Install Backend Dependencies

```bash
cd backend

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Step 4: Run Database Migrations

```bash
# Still in backend directory with poetry shell active

# Check current migration status
alembic current

# Run all migrations
alembic upgrade head

# Verify migrations applied
alembic current
# Should show: add_auto_parlay_tables (head)
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 84db2cfe5eb8, initial_schema
INFO  [alembic.runtime.migration] Running upgrade 84db2cfe5eb8 -> [hash], add_auto_parlay_tables
```

### Step 5: Verify Database Tables

```bash
# Connect to database
psql -U bet_better_user -d bet_better

# List all tables
\dt

# You should see these new tables:
# - alt_lines
# - game_props
# - prop_metadata
# - auto_parlay_requests
# - built_parlays
# - parlay_leg_explanations

# Check table structure
\d alt_lines
\d game_props

# Exit
\q
```

---

## 📊 Data Ingestion

### Step 1: Ingest Game Props (Spreads, Totals, Moneylines)

```bash
# Still in backend directory with poetry shell active

# Run game props ingestion
python -m scripts.ingest_game_props

# This will fetch:
# - Spreads and alternate spreads
# - Totals and alternate totals
# - Moneylines
# - First half lines
```

**Expected Output:**
```
INFO: Fetching NFL games from The Odds API...
INFO: Found 15 games for this week
INFO: Processing game: KC @ SF (Super Bowl LVIII)
INFO: Inserted spread: KC +2.5 (-110) / SF -2.5 (-110)
INFO: Inserted 5 alternate spreads
INFO: Inserted total: 47.5 O/U
INFO: Inserted 7 alternate totals
INFO: Inserted moneyline: KC +120 / SF -140
...
SUCCESS: Ingested 450 game props across 15 games
```

### Step 2: Ingest Player Props from FanDuel

```bash
# Run FanDuel data ingestion
python -m scripts.ingest_fanduel_data

# This will fetch all prop types:
# - Passing: yards, TDs, completions, longest, sacks
# - Rushing: yards, TDs, attempts, longest
# - Receiving: yards, TDs, receptions, longest
# - Scoring: anytime TD, first TD, last TD, 2+ TDs, 3+ TDs
# - Kicking: field goals made
```

**Expected Output:**
```
INFO: Fetching player props from FanDuel API...
INFO: Processing market: player_pass_yds (Passing Yards)
INFO: Found 32 QB props
INFO: Processing market: player_anytime_td (Anytime TD Scorer)
INFO: Found 156 player TD props
...
SUCCESS: Ingested 1,247 player props across 22 markets
```

### Step 3: Verify Data Ingestion

```bash
# Check data in database
psql -U bet_better_user -d bet_better

# Count player props by type
SELECT stat_type, COUNT(*) as count
FROM player_marginals
GROUP BY stat_type
ORDER BY count DESC;

# Expected results:
#  stat_type          | count
# -------------------+-------
#  anytime_tds       |   156
#  passing_yards     |    32
#  receiving_yards   |    94
#  rushing_yards     |    48
#  ...

# Check game props
SELECT * FROM game_props LIMIT 10;

# Check alt lines
SELECT * FROM alt_lines LIMIT 10;

# Exit
\q
```

---

## 🚀 Backend Startup

### Step 1: Start Backend Server

```bash
cd backend

# Ensure poetry shell is active
poetry shell

# Start server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or for production:
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Verify API Endpoints

Open browser or use curl:

```bash
# Check API health
curl http://localhost:8000/health

# Expected: {"status": "healthy"}

# Check API docs
open http://localhost:8000/docs

# Should see FastAPI interactive documentation

# Test auto-parlay endpoint
curl -X POST http://localhost:8000/api/v1/auto-parlay/build \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Build me a safe 5-leg parlay for the Super Bowl"
  }'

# Expected: JSON response with primary_parlay and alternatives
```

---

## 🎨 Frontend Setup

### Step 1: Install Frontend Dependencies

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Or if using yarn:
# yarn install
```

### Step 2: Configure Frontend Environment

```bash
# Create environment file
nano .env.local
```

**Add:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Step 3: Start Frontend Dev Server

```bash
# Still in frontend directory
npm run dev

# Or for production build:
# npm run build
# npm start
```

**Expected Output:**
```
  ▲ Next.js 14.1.0
  - Local:        http://localhost:3000
  - Network:      http://192.168.1.x:3000

✓ Ready in 2.3s
```

---

## 🧪 Testing the Complete System

### Test 1: Manual Parlay Builder (Sportsbook Mode)

1. **Open browser**: `http://localhost:3000/build-parlay`
2. **Click "Sportsbook" tab**
3. **Select a game** (e.g., "KC @ SF")
4. **Navigate to Parlay Builder**
5. **Add props** from different tabs:
   - Popular
   - Passing
   - Rushing
   - Receiving
   - TD Scorer
6. **Verify**:
   - Props load correctly
   - Betslip updates
   - Odds calculate properly
   - Copula correlation shows

**Expected**: All tabs show data, betslip works, odds are accurate

---

### Test 2: AI Auto-Parlay Builder

1. **Open browser**: `http://localhost:3000/build-parlay`
2. **Click "AI Builder" tab**
3. **Try Quick Presets**:
   - Click "🛡️ Safe Money"
   - Should auto-fill: "Build me a safe 5-leg parlay"
   - Click "Build My Parlay"

**Expected Output:**
```
✅ Optimized 5-Leg Parlay
+487 odds

Win Probability: 24.3%
Expected Value: $12.45
Confidence: 78%

I've built a 5-leg conservative picks with high confidence parlay...

LEG 1: Patrick Mahomes
OVER 285.5 Passing Yards (-110)
WHY THIS PICK: Patrick Mahomes has favorable matchup for Passing Yards
• Sharp money backing this (68%)
• Historical hit rate: 72%
```

4. **Try Custom Requests**:
   - "Build me a risky 7-leg parlay for the Super Bowl"
   - "Give me a cross-sport parlay (NFL + NBA)"
   - "Make me a same-game parlay for KC vs SF"

**Expected**: System returns optimized parlay with reasoning for each leg

---

### Test 3: Alternative Parlays

1. **After building a parlay**
2. **Scroll down** to "View Alternative Versions"
3. **Click to expand**

**Expected**: See 3 alternative parlays:
- 🛡️ Safer Version (higher win prob, lower variance)
- 🚀 Riskier Version (higher EV, more variance)
- 🎮 Same Game (all legs from one game)

---

### Test 4: All Prop Types

**Verify these prop types load:**

✅ **Passing Props**:
- Passing Yards
- Passing TDs
- Completions
- Longest Completion
- Interceptions
- Sacks Taken

✅ **Rushing Props**:
- Rushing Yards
- Rushing TDs
- Rush Attempts
- Longest Rush

✅ **Receiving Props**:
- Receiving Yards
- Receiving TDs
- Receptions
- Longest Reception

✅ **Scoring Props**:
- Anytime TD Scorer
- First TD Scorer
- Last TD Scorer
- 2+ TDs
- 3+ TDs

✅ **Game Props**:
- Spread
- Alternate Spreads
- Total
- Alternate Totals
- Moneyline
- Team Totals

---

## 🐛 Troubleshooting

### Issue: "No props available"

**Cause**: Data not ingested
**Fix**:
```bash
cd backend
poetry shell
python -m scripts.ingest_game_props
python -m scripts.ingest_fanduel_data
```

---

### Issue: "Database connection error"

**Cause**: PostgreSQL not running or wrong credentials
**Fix**:
```bash
# Start PostgreSQL
sudo service postgresql start

# Verify connection
psql -U bet_better_user -d bet_better

# Check .env file has correct DATABASE_URL
```

---

### Issue: "API endpoint 404"

**Cause**: Auto-parlay router not registered
**Fix**: Already fixed in `backend/app/main.py`
```python
from app.api.routes import auto_parlay
app.include_router(auto_parlay.router, prefix=f"/api/{settings.api_version}")
```

---

### Issue: "Frontend can't connect to API"

**Cause**: CORS or wrong API URL
**Fix**:
```bash
# Check frontend .env.local
cat frontend/.env.local
# Should have: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Check backend allows CORS
# In backend/app/main.py, verify:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Issue: "Migration fails"

**Cause**: Database schema conflicts
**Fix**:
```bash
# Drop and recreate database
psql -U postgres
DROP DATABASE bet_better;
CREATE DATABASE bet_better;
\q

# Run migrations fresh
alembic upgrade head
```

---

## 📊 Monitoring and Logs

### Backend Logs

```bash
# View live logs
cd backend
uvicorn app.main:app --reload --log-level debug

# Logs show:
# - API requests
# - Database queries
# - Auto-parlay build process
# - Errors and warnings
```

### Frontend Logs

```bash
# View browser console
# Open DevTools (F12) → Console tab

# Should see:
# - API call logs
# - Component render logs
# - Any errors or warnings
```

---

## 🎯 Production Deployment

### Environment Variables

**Backend `.env`:**
```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@prod-host:5432/bet_better
REDIS_URL=redis://prod-host:6379/0
SECRET_KEY=your_production_secret_key
ALLOWED_ORIGINS=https://yourdomain.com
```

**Frontend `.env.production`:**
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

### Docker Deployment (Optional)

```bash
# Build backend
cd backend
docker build -t bet-better-backend .

# Build frontend
cd ../frontend
docker build -t bet-better-frontend .

# Run with docker-compose
docker-compose up -d
```

---

## ✅ Verification Checklist

Before going live, verify:

- [ ] Database migrations applied successfully
- [ ] All game props ingested (spreads, totals, moneylines)
- [ ] All player props ingested (22 markets)
- [ ] Backend API returns 200 for `/health`
- [ ] Auto-parlay endpoint works: `/api/v1/auto-parlay/build`
- [ ] Frontend loads at `http://localhost:3000/build-parlay`
- [ ] AI Builder tab functions
- [ ] Sportsbook tab functions
- [ ] All prop tabs show data
- [ ] Betslip calculates odds correctly
- [ ] Alternative parlays generate
- [ ] Explanations show for each leg
- [ ] No console errors in browser
- [ ] No 500 errors in backend logs

---

## 🎉 Success Criteria

**You'll know the system is working when:**

1. ✅ You can type "Build me a safe 5-leg Super Bowl parlay"
2. ✅ System returns an optimized parlay in <2 seconds
3. ✅ Each leg has clear reasoning
4. ✅ Win probability, EV, and confidence are shown
5. ✅ Alternative versions (safer/riskier) are available
6. ✅ You can toggle between AI Builder and Sportsbook
7. ✅ All 22 prop markets load with data
8. ✅ Correlation analysis shows in betslip

---

## 🆘 Support

**If you encounter issues:**

1. **Check logs** (backend terminal and browser console)
2. **Verify data** (run SQL queries to check ingestion)
3. **Test endpoints** (use `/docs` for interactive API testing)
4. **Review error messages** (they're designed to be helpful)

**Common Commands:**
```bash
# Backend
cd backend && poetry shell && alembic current
python -m scripts.ingest_fanduel_data
uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Database
psql -U bet_better_user -d bet_better
```

---

**Last Updated**: February 1, 2026
**Status**: Ready for Production
**Next Steps**: Follow this guide to deploy and test the complete system
