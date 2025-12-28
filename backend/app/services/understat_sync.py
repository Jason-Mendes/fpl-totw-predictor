"""Service to sync xG/xA data from Understat."""

import asyncio
import logging
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session
from understatapi import UnderstatClient

from app.models import Player, PlayerGWStats

logger = logging.getLogger(__name__)


class UnderstatSyncService:
    """Service to fetch and sync xG data from Understat."""

    def __init__(self, db: Session):
        self.db = db
        self.understat = UnderstatClient()
        # Cache for player name matching
        self._player_match_cache: dict[str, int | None] = {}

    async def sync_xg_data(self, season: str = "2024") -> dict[str, Any]:
        """
        Sync xG data from Understat for all EPL players.

        Uses cumulative xG/xA data from Understat to compute per-game averages,
        then applies these averages to all player gameweek stats.

        Args:
            season: Season year (e.g., "2024" for 2024/25 season)

        Returns:
            Summary of sync results
        """
        results = {
            "players_matched": 0,
            "stats_updated": 0,
            "errors": [],
        }

        try:
            # Get all EPL players from Understat
            league_data = await self._get_league_players(season)
            logger.info(f"Fetched {len(league_data)} players from Understat")

            # Get FPL players for matching
            fpl_players = self.db.query(Player).all()
            fpl_by_name = {self._normalize_name(p.web_name): p for p in fpl_players}

            # Also create alternative mappings by full name
            for p in fpl_players:
                if p.first_name and p.second_name:
                    full_name = f"{p.first_name} {p.second_name}"
                    fpl_by_name[self._normalize_name(full_name)] = p

            # Process each Understat player
            for us_player in league_data:
                try:
                    fpl_player = self._match_player(us_player, fpl_by_name)
                    if not fpl_player:
                        continue

                    results["players_matched"] += 1

                    # Calculate per-game xG averages from cumulative stats
                    games = int(us_player.get("games", 0) or 0)
                    if games == 0:
                        continue

                    total_xg = float(us_player.get("xG", 0) or 0)
                    total_xa = float(us_player.get("xA", 0) or 0)
                    total_npxg = float(us_player.get("npxG", 0) or 0)

                    xg_per_game = total_xg / games
                    xa_per_game = total_xa / games
                    npxg_per_game = total_npxg / games

                    # Update all gameweek stats for this player with per-game averages
                    player_stats = (
                        self.db.query(PlayerGWStats)
                        .filter(PlayerGWStats.player_id == fpl_player.id)
                        .all()
                    )

                    for stats in player_stats:
                        # Scale xG by minutes played (per 90)
                        minutes = stats.minutes or 0
                        if minutes > 0:
                            scale = minutes / 90.0
                            stats.xg = round(xg_per_game * scale, 2)
                            stats.xa = round(xa_per_game * scale, 2)
                            stats.npxg = round(npxg_per_game * scale, 2)
                            results["stats_updated"] += 1

                except Exception as e:
                    results["errors"].append(f"Player {us_player.get('player_name')}: {e}")

            self.db.commit()

        except Exception as e:
            logger.error(f"Error syncing Understat data: {e}")
            results["errors"].append(str(e))

        logger.info(
            f"Understat sync complete: {results['players_matched']} players matched, "
            f"{results['stats_updated']} stats updated"
        )
        return results

    async def _get_league_players(self, season: str) -> list[dict]:
        """Get all EPL players from Understat."""
        try:
            teams_data = await asyncio.to_thread(
                lambda: self.understat.league(league="EPL").get_player_data(season=season)
            )
            return teams_data
        except Exception as e:
            logger.error(f"Error fetching EPL players: {e}")
            return []

    def _match_player(
        self, us_player: dict, fpl_by_name: dict[str, Player]
    ) -> Player | None:
        """Match Understat player to FPL player by name."""
        us_name = us_player.get("player_name", "")
        normalized = self._normalize_name(us_name)

        # Check cache first
        if normalized in self._player_match_cache:
            player_id = self._player_match_cache[normalized]
            if player_id:
                return self.db.query(Player).filter(Player.id == player_id).first()
            return None

        # Direct match
        if normalized in fpl_by_name:
            player = fpl_by_name[normalized]
            self._player_match_cache[normalized] = player.id
            return player

        # Fuzzy match
        best_match = None
        best_score = 0.0

        for fpl_name, player in fpl_by_name.items():
            score = SequenceMatcher(None, normalized, fpl_name).ratio()
            if score > best_score and score > 0.85:
                best_score = score
                best_match = player

        if best_match:
            self._player_match_cache[normalized] = best_match.id
            return best_match

        self._player_match_cache[normalized] = None
        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize player name for matching."""
        import unicodedata

        normalized = unicodedata.normalize("NFKD", name)
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))
        return normalized.lower().strip()


def sync_understat_data(db: Session, season: str = "2024") -> dict[str, Any]:
    """
    Synchronous wrapper to sync Understat data.

    Args:
        db: Database session
        season: Season year (e.g., "2024" for 2024/25 season)

    Returns:
        Sync results summary
    """
    service = UnderstatSyncService(db)
    return asyncio.run(service.sync_xg_data(season))
