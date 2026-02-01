# SmartParlay Setup Guide - AntiGravity Folder

## 📁 Your Current Folder Structure

```
/sessions/eloquent-blissful-ptolemy/mnt/Bet-Better/  ← Cursor folder (ignore this)
└── Bet-Better/  ← YOUR PROJECT (AntiGravity folder) - work here!
    ├── backend/
    ├── docs/
    ├── README.md
    ├── QUICKSTART.sh
    └── docker-compose.yml
```

**IMPORTANT**: Always work in `/sessions/eloquent-blissful-ptolemy/mnt/Bet-Better/Bet-Better/`

## 🚀 Quick Setup (3 Steps)

### Step 1: Get API Keys (~10 minutes)

You need 3 **FREE** API keys. Follow the detailed guide:

```bash
cat docs/API_KEYS_GUIDE.md
```

**Quick summary**:

1. **The Odds API** (https://the-odds-api.com/)
   - Sign up → Verify email → Copy API key
   - Free: 500 requests/month

2. **OpenWeatherMap** (https://openweathermap.org/api)
   - Sign up → Verify email → Copy API key from dashboard
   - Free: 1,000 calls/day

3. **MaxMind GeoLite2** (https://www.maxmind.com/en/geolite2/signup)
   - Sign up → Generate license key → Download database
   - Free: Unlimited (local database file)

### Step 2: Configure Environment

```bash
# Make sure you're in the RIGHT folder
cd /sessions/eloquent-blissful-ptolemy/mnt/Bet-Better/Bet-Better

# Create .env file
cp backend/.env.example backend/.env

# Edit with your API keys
nano backend/.env
# OR
code backend/.env  # if using VS Code
```

**Add your keys to `.env`**:
```bash
# The Odds API
ODDS_API_KEY=your-odds-api-key-here

# OpenWeatherMap
WEATHER_API_KEY=your-weather-api-key-here

# MaxMind GeoLite2
GEOIP_DB_PATH=/usr/share/GeoIP/GeoLite2-City.mmdb

# Database (leave as-is for now)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/smartparlay
REDIS_URL=redis://redis:6379/0

# Secret key (generate a secure one later, this is fine for dev)
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
```

### Step 3: Start Everything

```bash
# Make sure you're in the RIGHT folder
cd /sessions/eloquent-blissful-ptolemy/mnt/Bet-Better/Bet-Better

# Run the automated setup
./QUICKSTART.sh
```

**What this does**:
1. Checks Docker is installed
2. Checks for `.env` file
3. Starts all services (PostgreSQL, Redis, Backend, etc.)
4. Tests the JAX simulation engine
5. Tests regime detection

**Expected output**:
```
🎯 SmartParlay - Quick Start
==============================

✅ Docker found: Docker version 24.0.x
✅ Docker Compose found: docker-compose version 2.x
🚀 Starting services with Docker Compose...
⏳ Waiting for services to be ready...
🏥 Checking service health...
✅ Backend API is healthy

🧪 Running JAX Copula simulation benchmark...
   (First run will take ~2s for JIT compilation)

Running Student-t Copula simulation benchmark...

Results:
  First call (with JIT): 2143.5ms
  Second call (JIT cached): 45.2ms  ← This is what matters!
  Meets 150ms CPU target: True
  Probability estimate: 28.45%

✅ SmartParlay is ready!
```

## 🧪 Test It's Working

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "v1",
  "environment": "development"
}
```

### 2. Open API Documentation
Open in browser: http://localhost:8000/docs

You should see interactive API docs with all endpoints.

### 3. Test Simulation Engine
```bash
docker-compose exec backend python -m app.services.copula.simulation
```

Should show simulation benchmark results (~45ms after warmup).

### 4. Test Regime Detection
```bash
docker-compose exec backend python -m app.services.copula.regime
```

Should show 4 game regime examples (BLOWOUT, SHOOTOUT, DEFENSIVE, NORMAL).

## 📊 Services Running

After `./QUICKSTART.sh`, you'll have:

| Service | Port | URL |
|---------|------|-----|
| **Backend API** | 8000 | http://localhost:8000 |
| **API Docs** | 8000 | http://localhost:8000/docs |
| **PostgreSQL** | 5432 | localhost:5432 |
| **Redis** | 6379 | localhost:6379 |
| **Prometheus** | 9090 | http://localhost:9090 |
| **Grafana** | 3001 | http://localhost:3001 |

## 🔧 Useful Commands

```bash
# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f

# Stop everything
docker-compose down

# Restart backend only
docker-compose restart backend

# Get shell in backend container
docker-compose exec backend bash

# Check running containers
docker-compose ps

# Stop and remove all data (CAUTION!)
docker-compose down -v
```

## 🐛 Troubleshooting

### "Docker not found"
Install Docker Desktop:
- Mac: https://docs.docker.com/desktop/install/mac-install/
- Windows: https://docs.docker.com/desktop/install/windows-install/
- Linux: https://docs.docker.com/engine/install/

### "Backend API not responding"
```bash
# Check backend logs
docker-compose logs backend

# Common issue: Port 8000 already in use
# Solution: Stop other services using port 8000
lsof -ti:8000 | xargs kill -9

# Then restart
docker-compose restart backend
```

### "ModuleNotFoundError" or Python errors
```bash
# Rebuild backend container
docker-compose build backend

# Restart
docker-compose up -d
```

### "Permission denied" on QUICKSTART.sh
```bash
chmod +x QUICKSTART.sh
./QUICKSTART.sh
```

## 📚 What to Read Next

1. **README.md** - High-level project overview
2. **PROJECT_SUMMARY.md** - Complete build summary (30 pages)
3. **docs/API_KEYS_GUIDE.md** - Detailed API key setup
4. **DIRECTORY_STRUCTURE.md** - File organization

## 🎯 Next Steps After Setup

Once everything is running:

1. **Explore the API**: http://localhost:8000/docs
2. **Read the code**: Start with `backend/app/services/copula/simulation.py`
3. **Plan integration**: Decide when to integrate real odds API
4. **Design frontend**: Sketch out the user interface

## ✅ Setup Complete Checklist

- [ ] Got all 3 API keys (Odds API, Weather, GeoLite2)
- [ ] Created `backend/.env` with keys
- [ ] Ran `./QUICKSTART.sh` successfully
- [ ] Backend health check passes (http://localhost:8000/health)
- [ ] Simulation benchmark runs (<150ms)
- [ ] Can access API docs (http://localhost:8000/docs)

If all checked ✅, you're ready to start development!

## 🆘 Need Help?

**Issues with API keys?**
- Re-read: `docs/API_KEYS_GUIDE.md`
- Check: Did you verify email?
- Check: Did you copy the FULL key?

**Issues with Docker?**
- Run: `docker --version` and `docker-compose --version`
- Restart Docker Desktop if issues persist

**Issues with backend?**
- Run: `docker-compose logs backend`
- Look for error messages
- Check: Is `.env` file in `backend/` folder?

---

**You're working in**: `/sessions/eloquent-blissful-ptolemy/mnt/Bet-Better/Bet-Better/`

**Always use this command first**:
```bash
cd /sessions/eloquent-blissful-ptolemy/mnt/Bet-Better/Bet-Better
```

Good luck! 🚀
