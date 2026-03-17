# Quick Start Guide - Get Running in 10 Minutes

**Last Updated**: February 1, 2026

---

## ⚡ Super Quick Start (TL;DR)

```bash
# 1. Backend Setup
cd backend
poetry install
poetry shell
cp .env.example .env
# Edit .env with your database credentials
alembic upgrade head
python -m scripts.ingest_game_props
python -m scripts.ingest_fanduel_data
uvicorn app.main:app --reload

# 2. Frontend Setup (new terminal)
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev

# 3. Open browser
open http://localhost:3000/build-parlay
```

---

## 🎯 What You'll Get

After following this guide, you'll have:

✅ **AI Auto-Parlay Builder** - Type "Build me a safe 5-leg Super Bowl parlay" and get optimized results

✅ **Manual Sportsbook** - Browse games and props like FanDuel

✅ **All Prop Types** - 22 different markets (passing, rushing, receiving, TDs, spreads, totals, etc.)

✅ **Smart Recommendations** - System explains why each leg was chosen

✅ **Alternative Parlays** - Get safer/riskier/same-game versions

---

## 📋 Prerequisites

Make sure you have:
- Python 3.11+ (`python3 --version`)
- Node.js 18+ (`node --version`)
- PostgreSQL 14+ (`psql --version`)
- 10 minutes of time

---

## 🗄️ Step 1: Database Setup (2 minutes)

```bash
# Create database
psql -U postgres
CREATE DATABASE bet_better;
\q

# That's it!
```

---

## 🔧 Step 2: Backend Setup (3 minutes)

```bash
# Navigate to backend
cd backend

# Install dependencies
poetry install

# Activate environment
poetry shell

# Configure environment
cp .env.example .env

# Edit .env - UPDATE THESE:
# DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/bet_better
# SECRET_KEY=your_random_secret_key
# ODDS_API_KEY=your_odds_api_key (get from https://the-odds-api.com)

# Run migrations
alembic upgrade head

# Ingest data (this takes ~1-2 minutes)
python -m scripts.ingest_game_props
python -m scripts.ingest_fanduel_data

# Start server
uvicorn app.main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal running!**

---

## 🎨 Step 3: Frontend Setup (2 minutes)

**Open a new terminal:**

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start dev server
npm run dev
```

**You should see:**
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000

✓ Ready in 2.3s
```

**Keep this terminal running too!**

---

## 🎮 Step 4: Test It Out (3 minutes)

### Test 1: AI Auto-Parlay Builder

1. **Open**: http://localhost:3000/build-parlay

2. **Click "AI Builder" tab**

3. **Click "🛡️ Safe Money" preset**

4. **Click "Build My Parlay"**

**You should see:**
- Optimized 5-leg parlay with odds
- Win probability, Expected Value, Confidence
- Explanation for each leg
- Alternative versions (safer/riskier/same-game)

---

### Test 2: Manual Sportsbook

1. **Click "Sportsbook" tab**

2. **Select a game** (e.g., "KC @ SF")

3. **Try different prop tabs:**
   - Popular
   - Passing
   - Rushing
   - Receiving
   - TD Scorer

4. **Add props to betslip**

**You should see:**
- All prop types with data
- Betslip updating with odds
- Correlation analysis

---

## ✅ Success Checklist

If everything worked, you should be able to:

- [ ] Type "Build me a 5-leg parlay" → Get results in <2 seconds
- [ ] See explanations for each leg
- [ ] Get alternative parlay versions
- [ ] Switch between AI and Sportsbook modes
- [ ] See data in all prop tabs
- [ ] Add props to betslip
- [ ] See calculated parlay odds

---

## 🐛 Common Issues

### "No props available"

**Problem**: Data not ingested

**Fix**:
```bash
cd backend
poetry shell
python -m scripts.ingest_fanduel_data
```

---

### "Database connection error"

**Problem**: Wrong database URL in .env

**Fix**:
```bash
# Edit backend/.env
nano backend/.env

# Make sure DATABASE_URL is correct:
# DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bet_better
```

---

### "API 404 error"

**Problem**: Backend not running or wrong URL

**Fix**:
```bash
# Check backend is running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Check frontend .env.local
cat frontend/.env.local
# Should have: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

### "Frontend won't start"

**Problem**: Node modules not installed

**Fix**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 🧪 Run Automated Tests

Want to verify everything is working?

```bash
cd backend
poetry shell
python -m scripts.test_auto_parlay_system
```

This will run 5 comprehensive tests:
1. Intent Parser
2. Candidate Generation
3. Compatibility Engine
4. Parlay Scoring
5. Full Build (End-to-End)

**Expected output:**
```
🧪 AUTO-PARLAY SYSTEM TEST SUITE
====================================
...
📊 TEST SUMMARY
====================================
   Intent Parser: ✅ PASSED
   Candidate Generation: ✅ PASSED
   Compatibility Engine: ✅ PASSED
   Parlay Scoring: ✅ PASSED
   Full Build (E2E): ✅ PASSED

   Total: 5/5 tests passed

🎉 ALL TESTS PASSED! System is ready to use.
```

---

## 📚 What's Next?

### Try Different Queries

**Safe bets:**
- "Build me a super safe money parlay"
- "Give me a conservative 3-leg parlay"

**Risky bets:**
- "Build me a high-risk aggressive parlay"
- "Make me a degen lottery ticket"

**Specific games:**
- "Build a 5-leg parlay for the Super Bowl"
- "Give me a same-game parlay for KC vs SF"

**Cross-sport:**
- "Build a cross-sport parlay with NFL and NBA"

---

### Explore Features

**AI Builder:**
- Quick presets (Safe, Balanced, Risky, YOLO)
- Natural language input
- Alternative versions
- Detailed explanations

**Sportsbook:**
- Browse all games
- 22 prop types
- Player search
- Live correlation analysis

---

### Read Documentation

- **DEPLOYMENT_GUIDE.md** - Comprehensive deployment instructions
- **FIXES_APPLIED.md** - What was fixed and how
- **PHASE_2_COMPLETE.md** - Complete feature list
- **AUTO_PARLAY_ARCHITECTURE.md** - Deep technical dive

---

## 🎉 You're Done!

The system is now fully functional. You have:

✅ AI-powered parlay builder
✅ 22 different prop types
✅ FanDuel-style interface
✅ Smart recommendations with explanations
✅ Alternative parlay versions
✅ Unified AI + Sportsbook experience

**Enjoy building optimized parlays!** 🚀

---

## 💡 Pro Tips

1. **Data Freshness**: Re-run ingestion scripts daily to get latest odds
   ```bash
   python -m scripts.ingest_fanduel_data
   ```

2. **Quick Restart**: Use these aliases
   ```bash
   alias backend="cd backend && poetry shell && uvicorn app.main:app --reload"
   alias frontend="cd frontend && npm run dev"
   ```

3. **Monitor Logs**: Keep both terminal windows visible to see API calls and errors

4. **Test Often**: Run test suite after any changes
   ```bash
   python -m scripts.test_auto_parlay_system
   ```

---

**Questions or issues?** Check the troubleshooting section above or review the detailed DEPLOYMENT_GUIDE.md
