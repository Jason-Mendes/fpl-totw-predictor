"""FPL API client for fetching data from Fantasy Premier League."""

import logging
import time
from datetime import datetime
from typing import Any

import httpx

from app.config import get_settings
from app.constants import FPL_API_RATE_LIMIT_SECONDS, Position

logger = logging.getLogger(__name__)
settings = get_settings()


class FPLClient:
    """Client for interacting with the FPL API."""

    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request to the FPL API with rate limiting."""
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"Fetching {url}")

        # Rate limiting to be respectful to FPL servers
        time.sleep(FPL_API_RATE_LIMIT_SECONDS)

        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def get_bootstrap_static(self) -> dict[str, Any]:
        """
        Get bootstrap-static data containing:
        - elements: All players with their current data
        - teams: All teams
        - events: All gameweeks
        - element_types: Position types (GKP, DEF, MID, FWD)
        """
        return self._get("/bootstrap-static/")

    def get_fixtures(self, gameweek: int | None = None) -> list[dict[str, Any]]:
        """
        Get fixtures.

        Args:
            gameweek: Optional gameweek filter. If None, returns all fixtures.
        """
        if gameweek:
            return self._get(f"/fixtures/?event={gameweek}")
        return self._get("/fixtures/")

    def get_gameweek_live(self, gameweek: int) -> dict[str, Any]:
        """
        Get live data for a gameweek.

        Returns player stats for the gameweek including:
        - minutes, goals, assists, clean_sheets, etc.
        - bonus, bps (bonus points system)
        """
        return self._get(f"/event/{gameweek}/live/")

    def get_player_summary(self, player_id: int) -> dict[str, Any]:
        """
        Get detailed summary for a player.

        Returns:
        - history: Past gameweek performances
        - fixtures: Upcoming fixtures
        - history_past: Previous season summaries
        """
        return self._get(f"/element-summary/{player_id}/")

    def get_dream_team(self, gameweek: int) -> dict[str, Any]:
        """
        Get the Dream Team (Team of the Week) for a gameweek.

        Returns:
        - team: List of 11 players with highest points
        - top_player: Player of the week
        """
        return self._get(f"/dream-team/{gameweek}/")

    def get_set_piece_notes(self) -> list[dict[str, Any]]:
        """
        Get set piece taker notes for all teams.

        Returns info about penalty, corner, and free kick takers.
        """
        return self._get("/team/set-piece-notes/")

    def get_event_status(self) -> dict[str, Any]:
        """
        Get current event status.

        Useful for checking if bonus points are finalized.
        """
        return self._get("/event-status/")


def parse_fpl_datetime(dt_str: str | None) -> datetime | None:
    """Parse FPL datetime string to Python datetime."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def get_position_from_element_type(element_type: int) -> str:
    """Convert FPL element_type to position string using Position enum."""
    return Position.from_element_type(element_type).value
