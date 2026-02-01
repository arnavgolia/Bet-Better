"""
Database seeding script with sample NFL data.
Populates the database with teams, players, venues, and a sample game.
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.database import Team, Player, Venue, Game, PlayerMarginal, PlayerCorrelation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_database():
    """Seed database with sample NFL data."""
    
    engine = create_async_engine(str(settings.database_url))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        logger.info("🌱 Starting database seeding...")
        
        # ===== NFL TEAMS =====
        logger.info("Creating NFL teams...")
        
        teams_data = [
            {"name": "Los Angeles Rams", "abbreviation": "LAR", "city": "Los Angeles", "league": "NFL"},
            {"name": "Seattle Seahawks", "abbreviation": "SEA", "city": "Seattle", "league": "NFL"},
            {"name": "Kansas City Chiefs", "abbreviation": "KC", "city": "Kansas City", "league": "NFL"},
            {"name": "Buffalo Bills", "abbreviation": "BUF", "city": "Buffalo", "league": "NFL"},
            {"name": "San Francisco 49ers", "abbreviation": "SF", "city": "San Francisco", "league": "NFL"},
            {"name": "Philadelphia Eagles", "abbreviation": "PHI", "city": "Philadelphia", "league": "NFL"},
        ]
        
        teams = {}
        from sqlalchemy import select
        
        for team_data in teams_data:
            # Check if team exists
            stmt = select(Team).where(Team.abbreviation == team_data["abbreviation"])
            result = await session.execute(stmt)
            team = result.scalar_one_or_none()
            
            if not team:
                team = Team(**team_data)
                session.add(team)
                await session.flush()
                logger.info(f"Created team: {team.name}")
            else:
                logger.info(f"Found existing team: {team.name}")
            
            teams[team_data["abbreviation"]] = team
        
        logger.info(f"✅ Loaded {len(teams)} teams")
        
        # ===== VENUES =====
        logger.info("Creating venues...")
        
        sofi_stadium = Venue(
            name="SoFi Stadium",
            city="Inglewood",
            state="CA",
            is_dome=True,
            is_retractable=False,
            surface_type="fieldturf",
            latitude=33.9535,
            longitude=-118.3392
        )
        
        lumen_field = Venue(
            name="Lumen Field",
            city="Seattle",
            state="WA",
            is_dome=False,
            is_retractable=False,
            surface_type="fieldturf",
            latitude=47.5952,
            longitude=-122.3316
        )
        
        session.add_all([sofi_stadium, lumen_field])
        await session.flush()
        logger.info("✅ Created 2 venues")
        
        # ===== PLAYERS =====
        logger.info("Creating players...")
        
        players_data = [
            # Rams
            {"name": "Matthew Stafford", "team": "LAR", "position": "QB", "jersey_number": "9"},
            {"name": "Kyren Williams", "team": "LAR", "position": "RB", "jersey_number": "23"},
            {"name": "Cooper Kupp", "team": "LAR", "position": "WR", "jersey_number": "10"},
            {"name": "Puka Nacua", "team": "LAR", "position": "WR", "jersey_number": "17"},
            
            # Seahawks
            {"name": "Geno Smith", "team": "SEA", "position": "QB", "jersey_number": "7"},
            {"name": "Kenneth Walker III", "team": "SEA", "position": "RB", "jersey_number": "9"},
            {"name": "DK Metcalf", "team": "SEA", "position": "WR", "jersey_number": "14"},
            {"name": "Tyler Lockett", "team": "SEA", "position": "WR", "jersey_number": "16"},
        ]
        
        players = {}
        for player_data in players_data:
            team_abbr = player_data.pop("team")
            player = Player(
                **player_data,
                team_id=teams[team_abbr].id,
                injury_status="healthy"
            )
            session.add(player)
            players[player_data["name"]] = player
        
        await session.flush()
        logger.info(f"✅ Created {len(players)} players")
        
        # ===== GAME =====
        logger.info("Creating sample game...")
        
        # Game this Sunday
        game_time = datetime.now() + timedelta(days=(6 - datetime.now().weekday()) % 7)
        game_time = game_time.replace(hour=13, minute=0, second=0, microsecond=0)
        
        game = Game(
            sport="NFL",
            home_team_id=teams["LAR"].id,
            away_team_id=teams["SEA"].id,
            commence_time=game_time,
            venue_id=sofi_stadium.id,
            status="scheduled",
            spread=-3.5,  # Rams favored by 3.5
            total=48.5,
            temperature_f=72,  # Dome game
            wind_mph=0,
            precipitation_prob=0.0
        )
        
        session.add(game)
        await session.flush()
        logger.info("✅ Created 1 game")
        
        # ===== PLAYER MARGINALS (Betting Props) =====
        logger.info("Creating player prop bets...")
        
        marginals_data = [
            # Matthew Stafford
            {"player": "Matthew Stafford", "stat_type": "passing_yards", "mean": 270.0, "std_dev": 45.0, "line": 265.5, "over_odds": -110, "under_odds": -110},
            {"player": "Matthew Stafford", "stat_type": "passing_tds", "mean": 2.1, "std_dev": 0.9, "line": 1.5, "over_odds": -125, "under_odds": +105},
            
            # Kyren Williams
            {"player": "Kyren Williams", "stat_type": "rushing_yards", "mean": 82.0, "std_dev": 28.0, "line": 75.5, "over_odds": -115, "under_odds": -105},
            {"player": "Kyren Williams", "stat_type": "rushing_tds", "mean": 0.8, "std_dev": 0.6, "line": 0.5, "over_odds": +140, "under_odds": -170},
            
            # Cooper Kupp
            {"player": "Cooper Kupp", "stat_type": "receiving_yards", "mean": 88.0, "std_dev": 32.0, "line": 82.5, "over_odds": -110, "under_odds": -110},
            {"player": "Cooper Kupp", "stat_type": "receptions", "mean": 7.2, "std_dev": 2.1, "line": 6.5, "over_odds": -120, "under_odds": +100},
            
            # Geno Smith
            {"player": "Geno Smith", "stat_type": "passing_yards", "mean": 245.0, "std_dev": 50.0, "line": 242.5, "over_odds": -110, "under_odds": -110},
            
            # Kenneth Walker III
            {"player": "Kenneth Walker III", "stat_type": "rushing_yards", "mean": 68.0, "std_dev": 25.0, "line": 65.5, "over_odds": -110, "under_odds": -110},
            
            # DK Metcalf
            {"player": "DK Metcalf", "stat_type": "receiving_yards", "mean": 75.0, "std_dev": 30.0, "line": 72.5, "over_odds": -110, "under_odds": -110},
        ]
        
        for marginal_data in marginals_data:
            player_name = marginal_data.pop("player")
            player = players[player_name]
            
            # Calculate probabilities from normal distribution
            from scipy.stats import norm
            mean = marginal_data["mean"]
            std_dev = marginal_data["std_dev"]
            line = marginal_data["line"]
            
            # P(X > line) for over
            over_prob = 1 - norm.cdf(line, mean, std_dev)
            under_prob = 1 - over_prob
            
            marginal = PlayerMarginal(
                player_id=player.id,
                game_id=game.id,
                stat_type=marginal_data["stat_type"],
                mean=mean,
                std_dev=std_dev,
                line=line,
                over_probability=over_prob,
                under_probability=under_prob,
                over_odds=marginal_data.get("over_odds"),
                under_odds=marginal_data.get("under_odds"),
                source="seed_data"
            )
            session.add(marginal)
        
        await session.flush()
        logger.info(f"✅ Created {len(marginals_data)} player props")
        
        # ===== CORRELATIONS =====
        logger.info("Creating player correlations...")
        
        correlations_data = [
            # Stafford + Kupp (QB + WR1 = Strong Positive)
            {"p1": "Matthew Stafford", "s1": "passing_yards", "p2": "Cooper Kupp", "s2": "receiving_yards", "corr": 0.75},
            {"p1": "Matthew Stafford", "s1": "passing_tds", "p2": "Cooper Kupp", "s2": "receiving_yards", "corr": 0.60},
            
            # Stafford + Kyren Williams (QB + RB = Weak Negative or Neutral)
            {"p1": "Matthew Stafford", "s1": "passing_yards", "p2": "Kyren Williams", "s2": "rushing_yards", "corr": -0.15},
            
            # Stafford + Geno Smith (Opposing QBs = Positive/Shootout)
            {"p1": "Matthew Stafford", "s1": "passing_yards", "p2": "Geno Smith", "s2": "passing_yards", "corr": 0.45},
            
            # Geno + Metcalf (QB + WR1 = Strong Positive)
            {"p1": "Geno Smith", "s1": "passing_yards", "p2": "DK Metcalf", "s2": "receiving_yards", "corr": 0.72},
        ]
        
        count = 0
        for corr in correlations_data:
            p1 = players.get(corr["p1"])
            p2 = players.get(corr["p2"])
            
            if p1 and p2:
                # Store both directions (p1->p2 and p2->p1) for easier lookup
                c1 = PlayerCorrelation(
                    player_1_id=p1.id, player_2_id=p2.id,
                    stat_1=corr["s1"], stat_2=corr["s2"],
                    correlation=corr["corr"], sample_size=17
                )
                c2 = PlayerCorrelation(
                    player_1_id=p2.id, player_2_id=p1.id,
                    stat_1=corr["s2"], stat_2=corr["s1"],
                    correlation=corr["corr"], sample_size=17
                )
                session.add(c1)
                session.add(c2)
                count += 2

        await session.flush()
        logger.info(f"✅ Created {count} correlation entries")

        # Commit all changes
        await session.commit()
        logger.info("🎉 Database seeding complete!")
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("DATABASE SUMMARY:")
        logger.info(f"  Teams: {len(teams)}")
        logger.info(f"  Players: {len(players)}")
        logger.info(f"  Venues: 2")
        logger.info(f"  Games: 1")
        logger.info(f"  Player Props: {len(marginals_data)}")
        logger.info(f"  Correlations: {count}")
        logger.info("="*50)
        logger.info(f"\n📅 Sample Game: {teams['SEA'].name} @ {teams['LAR'].name}")
        logger.info(f"   Time: {game_time.strftime('%A, %B %d at %I:%M %p')}")
        logger.info(f"   Spread: LAR {game.spread}")
        logger.info(f"   Total: {game.total}")
        logger.info("="*50 + "\n")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
