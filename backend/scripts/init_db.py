"""
Database initialization and table creation script.
Run this to create all tables in PostgreSQL.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.database import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database tables."""
    logger.info(f"Connecting to database: {settings.database_url}")
    
    engine = create_async_engine(
        str(settings.database_url),
        echo=True,  # Show SQL queries
    )
    
    async with engine.begin() as conn:
        logger.info("Dropping all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    logger.info("✅ Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
