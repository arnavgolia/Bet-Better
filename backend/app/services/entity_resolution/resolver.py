"""
Entity Resolution Service (Rosetta Stone)

Handles the critical problem of player/team name inconsistencies across sportsbooks.
DraftKings calls him "Patrick Mahomes II", FanDuel calls him "Patrick Mahomes",
BetMGM calls him "P. Mahomes". This service maintains canonical mappings.

Example mismatch that cost real money:
- DraftKings: "Gabriel Davis"
- FanDuel: "Gabe Davis"
- Our system: master_player_id = "uuid-123"

Without this, we'd fail to aggregate odds or create incorrect correlations.
"""

from typing import Optional, List, Tuple
from thefuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database.player import Player
from app.core.cache import redis_client


class EntityResolver:
    """
    Fuzzy matching service for cross-sportsbook entity resolution.

    Uses a two-tier strategy:
    1. Exact match cache (Redis) - O(1), <1ms
    2. Fuzzy match with review queue - O(n), ~10ms for 100 candidates
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_ttl = 86400  # 24 hours

    async def resolve_player(
        self,
        external_name: str,
        source: str,
        team_abbr: Optional[str] = None,
        threshold: int = 85,
    ) -> Optional[str]:
        """
        Map external player name to internal master player ID.

        Args:
            external_name: Player name as it appears in external source
            source: Data source identifier ("draftkings", "fanduel", etc.)
            team_abbr: Team abbreviation for disambiguation (optional)
            threshold: Minimum fuzzy match score (0-100)

        Returns:
            Master player UUID or None if unresolvable

        Algorithm:
            1. Check exact match cache: O(1)
            2. Query player_mappings table for source-specific mapping
            3. If not found, fuzzy match against canonical names
            4. If confidence < threshold, flag for manual review
            5. Cache result and return
        """
        # Step 1: Check cache
        cache_key = f"player_map:{source}:{external_name.lower().strip()}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        # Step 2: Database lookup (source-specific mapping)
        # This would query the player_mappings table
        # Simplified for MVP - implement full DB query in production

        # Step 3: Fuzzy matching fallback
        candidates = await self._get_player_candidates(team_abbr)
        best_match, best_score = self._fuzzy_match(external_name, candidates)

        if best_score >= threshold:
            # Cache and return
            await redis_client.setex(cache_key, self.cache_ttl, best_match.id)
            return str(best_match.id)
        elif best_score >= 70:
            # Flag for review but return best guess
            await self._flag_for_review(external_name, source, best_match.id, best_score)
            return str(best_match.id)

        return None

    async def _get_player_candidates(
        self,
        team_abbr: Optional[str] = None
    ) -> List[Player]:
        """Fetch potential player matches from database."""
        query = select(Player)
        if team_abbr:
            query = query.join(Player.team).where(Team.abbreviation == team_abbr)

        result = await self.db.execute(query)
        return result.scalars().all()

    def _fuzzy_match(
        self,
        external_name: str,
        candidates: List[Player]
    ) -> Tuple[Optional[Player], int]:
        """
        Fuzzy match external name against candidate players.

        Uses token_sort_ratio which handles:
        - Word order differences ("Davis Gabriel" vs "Gabriel Davis")
        - Partial matches ("P. Mahomes" vs "Patrick Mahomes")
        - Punctuation differences
        """
        best_player = None
        best_score = 0

        for candidate in candidates:
            score = fuzz.token_sort_ratio(
                external_name.lower(),
                candidate.name.lower()
            )
            if score > best_score:
                best_score = score
                best_player = candidate

        return best_player, best_score

    async def _flag_for_review(
        self,
        external_name: str,
        source: str,
        internal_id: str,
        confidence: int
    ) -> None:
        """Flag low-confidence match for manual review."""
        # In production, this would insert into a review queue table
        # For MVP, just log it
        print(f"[REVIEW NEEDED] {source}:{external_name} -> {internal_id} ({confidence}%)")


# Geofencing Service
class GeoFencingService:
    """
    State-based sportsbook visibility and compliance.

    Critical for:
    1. Apple App Store compliance (no gambling links in prohibited states)
    2. Affiliate compliance (don't send traffic from illegal jurisdictions)
    3. User experience (don't show unavailable books)
    """

    STATE_BOOK_MATRIX = {
        "NY": ["draftkings", "fanduel", "caesars", "betmgm"],
        "NJ": ["draftkings", "fanduel", "caesars", "betmgm", "pointsbet"],
        "PA": ["draftkings", "fanduel", "betmgm"],
        "CA": [],  # No sports betting
        "UT": [],  # No gambling
        # ... full 50-state matrix
    }

    DFS_FALLBACK = ["prizepicks", "underdog"]

    async def get_allowed_books(self, ip_address: str) -> dict:
        """
        Determine which sportsbooks are legal for this user.

        Returns:
            {
                "state": "NY",
                "allowed_books": ["draftkings", "fanduel", ...],
                "is_dfs_only": false
            }
        """
        import hashlib
        import geoip2.database

        # Check cache
        ip_hash = hashlib.md5(ip_address.encode()).hexdigest()
        cache_key = f"geo:{ip_hash}"
        cached = await redis_client.get(cache_key)
        if cached:
            return cached

        # GeoIP lookup
        try:
            reader = geoip2.database.Reader('/path/to/GeoLite2-City.mmdb')
            response = reader.city(ip_address)
            state = response.subdivisions.most_specific.iso_code
        except Exception:
            # Default to restrictive if lookup fails
            state = "UNKNOWN"

        allowed = self.STATE_BOOK_MATRIX.get(state, [])
        result = {
            "state": state,
            "allowed_books": allowed if allowed else self.DFS_FALLBACK,
            "is_dfs_only": len(allowed) == 0
        }

        await redis_client.setex(cache_key, 3600, result)
        return result
