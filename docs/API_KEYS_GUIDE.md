# API Keys Setup Guide - FREE Tier Options

This guide shows you how to get all necessary API keys for the SmartParlay system **completely free**. Perfect for development, testing, and low-volume production use.

## 📋 Required APIs

| API | Free Tier | Monthly Limit | Signup Time |
|-----|-----------|---------------|-------------|
| The Odds API | ✅ Yes | 500 requests | 2 minutes |
| OpenWeatherMap | ✅ Yes | 1,000 calls/day | 2 minutes |
| MaxMind GeoLite2 | ✅ Yes | Unlimited | 5 minutes |

## 🎲 1. The Odds API (Sports Odds Data)

**What it provides**: Real-time odds from DraftKings, FanDuel, BetMGM, and 40+ sportsbooks.

### Sign Up Steps:

1. **Go to**: https://the-odds-api.com/

2. **Click "Get API Key"** (top right)

3. **Create Account**:
   - Email: `your-email@example.com`
   - Password: (create a secure password)
   - Click "Sign Up"

4. **Verify Email**: Check your inbox and click the verification link

5. **Get Your Key**:
   - Log in to dashboard: https://the-odds-api.com/account/
   - Your API key will be displayed at the top
   - Copy the key (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

6. **Add to .env**:
   ```bash
   ODDS_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

### Free Tier Limits:
- **500 requests/month**
- **500 odds/request**
- **All sports included**

### Usage Optimization Tips:
```python
# BAD: Polling every second (burns quota in minutes)
while True:
    fetch_odds()
    time.sleep(1)  # 💸 500 requests in 8 minutes!

# GOOD: Smart caching with 60s TTL
if cache_age > 60:
    fetch_odds()
    cache_with_ttl(60)
```

With smart caching, 500 requests = **~8 hours of continuous operation**.

### Test Your Key:

```bash
curl "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?apiKey=YOUR_KEY&regions=us&markets=h2h,spreads,totals&oddsFormat=american"
```

You should see JSON with NFL odds. Check remaining quota in response headers:
```
X-Requests-Remaining: 499
X-Requests-Used: 1
```

---

## ☁️ 2. OpenWeatherMap (Weather Data)

**What it provides**: Temperature, wind, precipitation for outdoor venues.

### Sign Up Steps:

1. **Go to**: https://openweathermap.org/api

2. **Click "Sign Up"** (top right)

3. **Create Account**:
   - Username: `your-username`
   - Email: `your-email@example.com`
   - Password: (create password)
   - Agree to terms, click "Create Account"

4. **Verify Email**: Check inbox and click verification link

5. **Get Your Key**:
   - Log in: https://home.openweathermap.org/
   - Go to "API keys" tab
   - Copy the "Default" key or create a new one
   - Key looks like: `abc123def456ghi789jkl012mno345pq`

6. **Add to .env**:
   ```bash
   WEATHER_API_KEY=abc123def456ghi789jkl012mno345pq
   ```

### Free Tier Limits:
- **1,000 calls/day** (~1 every 90 seconds)
- **60 calls/minute** burst capacity
- Current weather + 5-day forecast

### Usage Optimization:
```python
# Cache weather data for 1 hour (it doesn't change that fast)
WEATHER_CACHE_TTL = 3600

# Only fetch for outdoor venues
if game.venue.is_outdoor:
    weather = get_weather_cached(game.venue.lat, game.venue.lon)
```

With caching, 1,000 calls/day = **dozens of games per day**.

### Test Your Key:

```bash
# Get weather for Lambeau Field (Green Bay, WI)
curl "https://api.openweathermap.org/data/2.5/weather?lat=44.5013&lon=-88.0622&appid=YOUR_KEY&units=imperial"
```

You should see:
```json
{
  "main": {
    "temp": 35.6,
    "feels_like": 28.4
  },
  "wind": {
    "speed": 12.66
  },
  ...
}
```

---

## 🌍 3. MaxMind GeoLite2 (Geolocation Database)

**What it provides**: IP → State mapping for compliance/geofencing.

### Sign Up Steps:

1. **Go to**: https://www.maxmind.com/en/geolite2/signup

2. **Create Account**:
   - Email: `your-email@example.com`
   - Password: (create password)
   - Check "I will use GeoLite2 for free"
   - Agree to terms, click "Continue"

3. **Verify Email**: Click verification link

4. **Generate License Key**:
   - Log in: https://www.maxmind.com/en/account/login
   - Go to "My License Key" (left sidebar)
   - Click "Generate new license key"
   - Description: "SmartParlay Dev"
   - **IMPORTANT**: Select "No" for "Will this key be used for GeoIP Update?"
   - Click "Confirm"
   - **Copy the key immediately** (only shown once!)

5. **Download Database**:
   ```bash
   # Install geoipupdate tool
   sudo apt-get install geoipupdate  # Ubuntu/Debian
   # OR
   brew install geoipupdate  # macOS

   # Configure
   cat > /usr/local/etc/GeoIP.conf <<EOF
   AccountID YOUR_ACCOUNT_ID
   LicenseKey YOUR_LICENSE_KEY
   EditionIDs GeoLite2-City
   EOF

   # Download database
   geoipupdate

   # Database will be at: /usr/share/GeoIP/GeoLite2-City.mmdb
   ```

6. **Add to .env**:
   ```bash
   GEOIP_DB_PATH=/usr/share/GeoIP/GeoLite2-City.mmdb
   ```

### Free Tier Limits:
- **Unlimited lookups** (it's a local database file!)
- **Weekly updates** to database
- City-level precision

### Test Your Database:

```python
import geoip2.database

reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-City.mmdb')
response = reader.city('8.8.8.8')  # Google DNS

print(f"State: {response.subdivisions.most_specific.iso_code}")
# Output: State: CA (California)
```

---

## 🔌 Alternative/Backup Free APIs

### SportsDataIO (Backup Odds Source)
- **Free Tier**: 1,000 calls/month
- **Signup**: https://sportsdata.io/
- **Use Case**: Backup if The Odds API quota exhausted

### RapidAPI Sports APIs
- **Various Providers**: Search "sports odds" on https://rapidapi.com/
- **Free Tiers**: 50-500 calls/month depending on provider
- **Use Case**: Supplemental data sources

---

## 💡 Pro Tips for Free Tier Usage

### 1. Implement Aggressive Caching

```python
# Redis cache with TTL
CACHE_STRATEGY = {
    "odds_main_lines": 60,      # 60s for spread/total/ML
    "odds_player_props": 120,   # 2 min for props (change slower)
    "weather": 3600,            # 1 hour (doesn't change fast)
    "geoip": 86400,             # 24 hours (IP location stable)
}
```

### 2. Lazy Loading

```python
# DON'T fetch odds for all games on page load
# DO fetch only when user clicks on a specific game

@router.get("/games")
async def list_games():
    # Return games WITHOUT odds (just names, times)
    return {"games": [...]}

@router.get("/games/{game_id}/odds")
async def get_game_odds(game_id: str):
    # Fetch odds ONLY when user opens this game
    return await fetch_odds_cached(game_id)
```

### 3. Request Deduplication

```python
# If 10 users request same game within 60s, fetch once
from asyncio import Lock

game_locks = {}

async def get_odds_deduplicated(game_id):
    if game_id not in game_locks:
        game_locks[game_id] = Lock()

    async with game_locks[game_id]:
        # Check cache first
        cached = await redis.get(f"odds:{game_id}")
        if cached:
            return cached

        # Fetch from API (only one request for all concurrent users)
        odds = await external_api.fetch(game_id)
        await redis.setex(f"odds:{game_id}", 60, odds)
        return odds
```

### 4. Monitor Your Quota

```python
# Add quota tracking middleware
from fastapi import Request

@app.middleware("http")
async def track_api_usage(request: Request, call_next):
    response = await call_next(request)

    if "odds-api" in str(request.url):
        remaining = response.headers.get("X-Requests-Remaining")
        if remaining and int(remaining) < 50:
            # Send alert!
            await send_slack_alert(f"⚠️ Only {remaining} Odds API requests left!")

    return response
```

---

## 🚀 Production Upgrade Path

When you're ready to scale beyond free tiers:

### The Odds API Pro Tiers:
- **Starter**: $99/mo - 10,000 requests
- **Hobby**: $249/mo - 50,000 requests
- **Professional**: $999/mo - 500,000 requests

### Cost Projection:
```
Free Tier:  500 requests/mo    → ~50 users/month
Starter:    10,000 requests/mo → ~1,000 users/month
Hobby:      50,000 requests/mo → ~5,000 users/month

Assumptions:
- 10 parlay generations per user per month
- Smart caching reduces odds API calls by 80%
```

---

## ✅ Verification Checklist

Before running the application, verify all keys work:

```bash
cd backend
python scripts/verify_api_keys.py
```

Expected output:
```
✓ The Odds API: Connected (499 requests remaining)
✓ OpenWeatherMap: Connected (999 requests remaining today)
✓ MaxMind GeoLite2: Database loaded (1,234,567 records)

All API keys verified successfully!
```

---

## 🆘 Troubleshooting

### "API key invalid"
- Double-check you copied the entire key (no spaces)
- Make sure key is in `.env` file, not `.env.example`
- Restart backend after changing `.env`

### "Rate limit exceeded"
- Check your usage dashboard on provider website
- Implement caching if not done yet
- Consider request deduplication

### "GeoIP database not found"
- Run `geoipupdate` to download database
- Check path in `.env` matches actual file location
- On macOS, try `/usr/local/share/GeoIP/` instead of `/usr/share/GeoIP/`

### "Weather API 401 Unauthorized"
- OpenWeatherMap keys take ~10 minutes to activate after signup
- Try again in 15 minutes
- Check you're using correct endpoint (v2.5, not v3)

---

## 📧 Support

If you encounter issues:
1. Check provider's documentation (links above)
2. Verify API key in provider dashboard
3. Test with `curl` commands provided above
4. Check application logs for detailed error messages

---

**Next Steps**: Once you have all keys configured, proceed to [Deployment Guide](DEPLOYMENT.md).
