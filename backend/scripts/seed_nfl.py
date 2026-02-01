"""
Seed all 32 NFL teams.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())

from app.models.database import Team
from app.api.dependencies.database import async_session_maker

teams_data = [
    # AFC East
    {"name": "Buffalo Bills", "abbrev": "BUF", "city": "Buffalo"},
    {"name": "Miami Dolphins", "abbrev": "MIA", "city": "Miami"},
    {"name": "New England Patriots", "abbrev": "NE", "city": "Foxborough"},
    {"name": "New York Jets", "abbrev": "NYJ", "city": "New York"},
    # AFC North
    {"name": "Baltimore Ravens", "abbrev": "BAL", "city": "Baltimore"},
    {"name": "Cincinnati Bengals", "abbrev": "CIN", "city": "Cincinnati"},
    {"name": "Cleveland Browns", "abbrev": "CLE", "city": "Cleveland"},
    {"name": "Pittsburgh Steelers", "abbrev": "PIT", "city": "Pittsburgh"},
    # AFC South
    {"name": "Houston Texans", "abbrev": "HOU", "city": "Houston"},
    {"name": "Indianapolis Colts", "abbrev": "IND", "city": "Indianapolis"},
    {"name": "Jacksonville Jaguars", "abbrev": "JAX", "city": "Jacksonville"},
    {"name": "Tennessee Titans", "abbrev": "TEN", "city": "Nashville"},
    # AFC West
    {"name": "Denver Broncos", "abbrev": "DEN", "city": "Denver"},
    {"name": "Kansas City Chiefs", "abbrev": "KC", "city": "Kansas City"},
    {"name": "Las Vegas Raiders", "abbrev": "LV", "city": "Las Vegas"},
    {"name": "Los Angeles Chargers", "abbrev": "LAC", "city": "Los Angeles"},
    # NFC East
    {"name": "Dallas Cowboys", "abbrev": "DAL", "city": "Dallas"},
    {"name": "New York Giants", "abbrev": "NYG", "city": "New York"},
    {"name": "Philadelphia Eagles", "abbrev": "PHI", "city": "Philadelphia"},
    {"name": "Washington Commanders", "abbrev": "WAS", "city": "Washington"},
    # NFC North
    {"name": "Chicago Bears", "abbrev": "CHI", "city": "Chicago"},
    {"name": "Detroit Lions", "abbrev": "DET", "city": "Detroit"},
    {"name": "Green Bay Packers", "abbrev": "GB", "city": "Green Bay"},
    {"name": "Minnesota Vikings", "abbrev": "MIN", "city": "Minnesota"},
    # NFC South
    {"name": "Atlanta Falcons", "abbrev": "ATL", "city": "Atlanta"},
    {"name": "Carolina Panthers", "abbrev": "CAR", "city": "Charlotte"},
    {"name": "New Orleans Saints", "abbrev": "NO", "city": "New Orleans"},
    {"name": "Tampa Bay Buccaneers", "abbrev": "TB", "city": "Tampa"},
    # NFC West
    {"name": "Arizona Cardinals", "abbrev": "ARI", "city": "Phoenix"},
    {"name": "Los Angeles Rams", "abbrev": "LAR", "city": "Los Angeles"},
    {"name": "San Francisco 49ers", "abbrev": "SF", "city": "San Francisco"},
    {"name": "Seattle Seahawks", "abbrev": "SEA", "city": "Seattle"},
]

async def seed_teams():
    print("Seeding NFL Teams...")
    async with async_session_maker() as db:
        for t in teams_data:
            # Check existing
            # We can't query by name easily without select
            # For simplicity, if database is fresh-ish, we just add or ignore unique constraint error
            # But robust way:
            from sqlalchemy import select
            stmt = select(Team).where(Team.name == t["name"])
            existing = (await db.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                team = Team(
                    name=t["name"],
                    abbreviation=t["abbrev"],
                    city=t["city"],
                    league="NFL",
                    created_at=datetime.utcnow()
                )
                db.add(team)
                print(f"Added {t['name']}")
            else:
                print(f"Skipped {t['name']} (Exists)")
        
        await db.commit()
    print("Done")

if __name__ == "__main__":
    asyncio.run(seed_teams())
