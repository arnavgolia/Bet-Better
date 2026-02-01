"""
Seed Super Bowl LX player props
Adds realistic player props for the 2026 Super Bowl
"""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from app.core.config import settings
from app.models.database import Player, PlayerMarginal, Team, Game
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




async def seed_super_bowl_props():
    """Seed Super Bowl player props"""
    # Create async engine and session
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        # Find the Super Bowl game (Feb 8, 2026)
        result = await session.execute(
            select(Game)
            .options(selectinload(Game.home_team), selectinload(Game.away_team))
            .where(Game.commence_time >= datetime(2026, 2, 8))
        )
        super_bowl = result.scalar_one_or_none()
        
        if not super_bowl:
            logger.error("Super Bowl game not found!")
            return
        
        logger.info(f"Found Super Bowl: {super_bowl.away_team.name} @ {super_bowl.home_team.name}")
        
        # Get teams
        seahawks_id = super_bowl.away_team.id
        patriots_id = super_bowl.home_team.id
        
        # Create Super Bowl players
        players_data = [
            # Seahawks
            {"name": "Geno Smith", "team_id": seahawks_id, "position": "QB", "jersey_number": "7"},
            {"name": "Kenneth Walker III", "team_id": seahawks_id, "position": "RB", "jersey_number": "9"},
            {"name": "DK Metcalf", "team_id": seahawks_id, "position": "WR", "jersey_number": "14"},
            {"name": "Tyler Lockett", "team_id": seahawks_id, "position": "WR", "jersey_number": "16"},
            {"name": "Jaxon Smith-Njigba", "team_id": seahawks_id, "position": "WR", "jersey_number": "11"},
            
            # Patriots
            {"name": "Drake Maye", "team_id": patriots_id, "position": "QB", "jersey_number": "10"},
            {"name": "Rhamondre Stevenson", "team_id": patriots_id, "position": "RB", "jersey_number": "38"},
            {"name": "Kendrick Bourne", "team_id": patriots_id, "position": "WR", "jersey_number": "84"},
            {"name": "DeMario Douglas", "team_id": patriots_id, "position": "WR", "jersey_number": "3"},
            {"name": "Hunter Henry", "team_id": patriots_id, "position": "TE", "jersey_number": "85"},
        ]
        
        players = []
        for p_data in players_data:
            # Check if player exists
            result = await session.execute(
                select(Player).where(
                    Player.name == p_data["name"],
                    Player.team_id == p_data["team_id"]
                )
            )
            player = result.scalar_one_or_none()
            
            if not player:
                player = Player(**p_data)
                session.add(player)
                await session.flush()
                logger.info(f"Created player: {player.name}")
            else:
                logger.info(f"Player exists: {player.name}")
            
            players.append(player)
        
        await session.commit()
        
        # Create player props
        props_data = [
            # Geno Smith
            {"player": players[0], "stat_type": "passing_yards", "line": 265.5, "mean": 272.0, "std_dev": 55.0},
            {"player": players[0], "stat_type": "passing_tds", "line": 1.5, "mean": 1.8, "std_dev": 1.1},
            {"player": players[0], "stat_type": "completions", "line": 22.5, "mean": 24.0, "std_dev": 4.5},
            
            # Kenneth Walker III
            {"player": players[1], "stat_type": "rushing_yards", "line": 75.5, "mean": 82.0, "std_dev": 28.0},
            {"player": players[1], "stat_type": "rushing_attempts", "line": 16.5, "mean": 18.0, "std_dev": 4.0},
            
            # DK Metcalf
            {"player": players[2], "stat_type": "receiving_yards", "line": 68.5, "mean": 74.0, "std_dev": 30.0},
            {"player": players[2], "stat_type": "receptions", "line": 4.5, "mean": 5.2, "std_dev": 2.0},
            
            # Tyler Lockett
            {"player": players[3], "stat_type": "receiving_yards", "line": 52.5, "mean": 58.0, "std_dev": 25.0},
            {"player": players[3], "stat_type": "receptions", "line": 4.5, "mean": 5.0, "std_dev": 1.8},
            
            # Jaxon Smith-Njigba
            {"player": players[4], "stat_type": "receiving_yards", "line": 45.5, "mean": 50.0, "std_dev": 22.0},
            
            # Drake Maye
            {"player": players[5], "stat_type": "passing_yards", "line": 245.5, "mean": 255.0, "std_dev": 60.0},
            {"player": players[5], "stat_type": "passing_tds", "line": 1.5, "mean": 1.6, "std_dev": 1.0},
            
            # Rhamondre Stevenson
            {"player": players[6], "stat_type": "rushing_yards", "line": 65.5, "mean": 72.0, "std_dev": 26.0},
            {"player": players[6], "stat_type": "receptions", "line": 3.5, "mean": 4.0, "std_dev": 1.5},
            
            # Kendrick Bourne
            {"player": players[7], "stat_type": "receiving_yards", "line": 48.5, "mean": 54.0, "std_dev": 24.0},
            
            # DeMario Douglas
            {"player": players[8], "stat_type": "receiving_yards", "line": 42.5, "mean": 48.0, "std_dev": 20.0},
            
            # Hunter Henry
            {"player": players[9], "stat_type": "receiving_yards", "line": 38.5, "mean": 42.0, "std_dev": 18.0},
            {"player": players[9], "stat_type": "receptions", "line": 3.5, "mean": 4.2, "std_dev": 1.6},
        ]
        
        for prop_data in props_data:
            player = prop_data.pop("player")
            
            # Calculate probabilities using normal distribution
            from scipy.stats import norm
            z_score = (prop_data["line"] - prop_data["mean"]) / prop_data["std_dev"]
            under_prob = norm.cdf(z_score)
            over_prob = 1 - under_prob
            
            prop = PlayerMarginal(
                game_id=super_bowl.id,
                player_id=player.id,
                over_probability=over_prob,
                under_probability=under_prob,
                over_odds=-110.0,
                under_odds=-110.0,
                **prop_data
            )
            session.add(prop)
        
        await session.commit()
        logger.info(f"✅ Created {len(props_data)} Super Bowl player props")
        
        logger.info("\n" + "="*50)
        logger.info("SUPER BOWL LX PROPS SEEDED!")
        logger.info(f"Game: {super_bowl.away_team.name} @ {super_bowl.home_team.name}")
        logger.info(f"Date: {super_bowl.commence_time}")
        logger.info(f"Total Props: {len(props_data)}")
        logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(seed_super_bowl_props())
