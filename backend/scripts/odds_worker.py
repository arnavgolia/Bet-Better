"""
Background worker to fetch and update odds periodically.
Usage: python -m scripts.odds_worker
"""

import asyncio
import logging
import sys
import os

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.api.dependencies.database import async_session_maker
from app.services.odds.ingest import fetch_and_update_nfl_odds

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("odds_worker")


async def run_loop():
    logger.info("Starting Odds Ingestion Worker")
    logger.info("Press Ctrl+C to stop")
    
    while True:
        try:
            logger.info("Starting ingestion cycle...")
            async with async_session_maker() as db:
                await fetch_and_update_nfl_odds(db)
            logger.info("Ingestion cycle finished successfully.")
        except Exception as e:
            logger.error(f"Error in worker cycle: {e}", exc_info=True)
        
        # Determine sleep time (e.g. 15 minutes) calls used:
        # Mock mode: cheap. Real API: expensive.
        # Use short sleep for demo.
        sleep_seconds = 60 * 15  # 15 minutes
        logger.info(f"Sleeping for {sleep_seconds} seconds...")
        await asyncio.sleep(sleep_seconds)


if __name__ == "__main__":
    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
