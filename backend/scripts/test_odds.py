"""
Fetch odds ONCE for testing.
"""
import asyncio
import logging
import sys
import os

sys.path.append(os.getcwd())

from app.api.dependencies.database import async_session_maker
from app.services.odds.ingest import fetch_and_update_nfl_odds

logging.basicConfig(level=logging.INFO)

async def main():
    print("Running Single Odds Update...")
    async with async_session_maker() as db:
        await fetch_and_update_nfl_odds(db)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
