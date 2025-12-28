"""Data ingestion service for syncing FPL data to database."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    DreamTeam,
    Fixture,
    Gameweek,
    Player,
    PlayerGWStats,
    Team,
)
from app.services.fpl_client import (
    FPLClient,
    get_position_from_element_type,
    parse_fpl_datetime,
)

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting FPL data into the database."""

    def __init__(self, db: Session):
        self.db = db
        self.fpl_client = FPLClient()

    def close(self):
        """Clean up resources."""
        self.fpl_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def sync_all(self) -> dict[str, int]:
        """
        Sync all FPL data.

        Returns dict with counts of synced records.
        """
        logger.info("Starting full FPL data sync")

        # Get bootstrap data (teams, players, gameweeks)
        bootstrap = self.fpl_client.get_bootstrap_static()

        # Sync in order (due to foreign key dependencies)
        teams_count = self._sync_teams(bootstrap["teams"])
        gameweeks_count = self._sync_gameweeks(bootstrap["events"])
        players_count = self._sync_players(bootstrap["elements"])
        fixtures_count = self._sync_fixtures()
        stats_count = self._sync_all_player_stats()
        dream_team_count = self._sync_all_dream_teams()

        # Sync set piece takers
        self._sync_set_piece_takers()

        self.db.commit()

        return {
            "teams": teams_count,
            "gameweeks": gameweeks_count,
            "players": players_count,
            "fixtures": fixtures_count,
            "player_stats": stats_count,
            "dream_teams": dream_team_count,
        }

    def _sync_teams(self, teams_data: list[dict[str, Any]]) -> int:
        """Sync teams from FPL data."""
        logger.info(f"Syncing {len(teams_data)} teams")
        count = 0

        for team_data in teams_data:
            team = self.db.query(Team).filter(Team.fpl_id == team_data["id"]).first()

            if not team:
                team = Team(fpl_id=team_data["id"])
                self.db.add(team)

            team.name = team_data["name"]
            team.short_name = team_data["short_name"]
            team.strength_attack_home = team_data.get("strength_attack_home")
            team.strength_attack_away = team_data.get("strength_attack_away")
            team.strength_defence_home = team_data.get("strength_defence_home")
            team.strength_defence_away = team_data.get("strength_defence_away")
            count += 1

        self.db.flush()
        logger.info(f"Synced {count} teams")
        return count

    def _sync_gameweeks(self, events_data: list[dict[str, Any]]) -> int:
        """Sync gameweeks from FPL data."""
        logger.info(f"Syncing {len(events_data)} gameweeks")
        count = 0

        for event_data in events_data:
            gw = (
                self.db.query(Gameweek)
                .filter(Gameweek.fpl_id == event_data["id"])
                .first()
            )

            if not gw:
                gw = Gameweek(fpl_id=event_data["id"])
                self.db.add(gw)

            gw.name = event_data.get("name")
            gw.deadline = parse_fpl_datetime(event_data.get("deadline_time"))
            gw.finished = event_data.get("finished", False)
            gw.is_current = event_data.get("is_current", False)
            gw.is_next = event_data.get("is_next", False)
            count += 1

        self.db.flush()
        logger.info(f"Synced {count} gameweeks")
        return count

    def _sync_players(self, elements_data: list[dict[str, Any]]) -> int:
        """Sync players from FPL data."""
        logger.info(f"Syncing {len(elements_data)} players")
        count = 0

        # Build team fpl_id to db id mapping
        teams = self.db.query(Team).all()
        team_map = {t.fpl_id: t.id for t in teams}

        for elem_data in elements_data:
            player = (
                self.db.query(Player).filter(Player.fpl_id == elem_data["id"]).first()
            )

            if not player:
                player = Player(fpl_id=elem_data["id"])
                self.db.add(player)

            player.team_id = team_map.get(elem_data["team"])
            player.web_name = elem_data["web_name"]
            player.first_name = elem_data.get("first_name")
            player.second_name = elem_data.get("second_name")
            player.position = get_position_from_element_type(elem_data["element_type"])
            player.now_cost = elem_data.get("now_cost")
            player.status = elem_data.get("status")
            player.chance_of_playing = elem_data.get("chance_of_playing_next_round")
            player.news = elem_data.get("news")
            count += 1

        self.db.flush()
        logger.info(f"Synced {count} players")
        return count

    def _sync_fixtures(self) -> int:
        """Sync all fixtures."""
        fixtures_data = self.fpl_client.get_fixtures()
        logger.info(f"Syncing {len(fixtures_data)} fixtures")
        count = 0

        # Build mappings
        teams = self.db.query(Team).all()
        team_map = {t.fpl_id: t.id for t in teams}
        gameweeks = self.db.query(Gameweek).all()
        gw_map = {g.fpl_id: g.id for g in gameweeks}

        for fix_data in fixtures_data:
            fixture = (
                self.db.query(Fixture).filter(Fixture.fpl_id == fix_data["id"]).first()
            )

            if not fixture:
                fixture = Fixture(fpl_id=fix_data["id"])
                self.db.add(fixture)

            fixture.gameweek_id = gw_map.get(fix_data.get("event"))
            fixture.team_home_id = team_map[fix_data["team_h"]]
            fixture.team_away_id = team_map[fix_data["team_a"]]
            fixture.kickoff_time = parse_fpl_datetime(fix_data.get("kickoff_time"))
            fixture.difficulty_home = fix_data.get("team_h_difficulty")
            fixture.difficulty_away = fix_data.get("team_a_difficulty")
            fixture.team_h_score = fix_data.get("team_h_score")
            fixture.team_a_score = fix_data.get("team_a_score")
            fixture.finished = fix_data.get("finished", False)
            count += 1

        self.db.flush()
        logger.info(f"Synced {count} fixtures")
        return count

    def _sync_all_player_stats(self) -> int:
        """Sync player stats for all finished gameweeks."""
        finished_gws = (
            self.db.query(Gameweek).filter(Gameweek.finished == True).all()  # noqa: E712
        )
        logger.info(f"Syncing player stats for {len(finished_gws)} finished gameweeks")

        total_count = 0
        for gw in finished_gws:
            count = self._sync_gameweek_stats(gw.fpl_id)
            total_count += count

        return total_count

    def _sync_gameweek_stats(self, gw_fpl_id: int) -> int:
        """Sync player stats for a single gameweek."""
        live_data = self.fpl_client.get_gameweek_live(gw_fpl_id)
        elements = live_data.get("elements", [])

        # Build mappings
        players = self.db.query(Player).all()
        player_map = {p.fpl_id: p.id for p in players}
        gw = self.db.query(Gameweek).filter(Gameweek.fpl_id == gw_fpl_id).first()
        if not gw:
            return 0

        count = 0
        for elem in elements:
            player_fpl_id = elem["id"]
            player_db_id = player_map.get(player_fpl_id)
            if not player_db_id:
                continue

            stats = elem.get("stats", {})
            if stats.get("minutes", 0) == 0:
                # Skip players who didn't play
                continue

            # Check if stats already exist
            existing = (
                self.db.query(PlayerGWStats)
                .filter(
                    PlayerGWStats.player_id == player_db_id,
                    PlayerGWStats.gameweek_id == gw.id,
                )
                .first()
            )

            if not existing:
                existing = PlayerGWStats(player_id=player_db_id, gameweek_id=gw.id)
                self.db.add(existing)

            # Update stats
            existing.minutes = stats.get("minutes", 0)
            existing.goals_scored = stats.get("goals_scored", 0)
            existing.assists = stats.get("assists", 0)
            existing.clean_sheets = stats.get("clean_sheets", 0)
            existing.goals_conceded = stats.get("goals_conceded", 0)
            existing.own_goals = stats.get("own_goals", 0)
            existing.penalties_saved = stats.get("penalties_saved", 0)
            existing.penalties_missed = stats.get("penalties_missed", 0)
            existing.yellow_cards = stats.get("yellow_cards", 0)
            existing.red_cards = stats.get("red_cards", 0)
            existing.saves = stats.get("saves", 0)
            existing.bonus = stats.get("bonus", 0)
            existing.bps = stats.get("bps", 0)
            existing.total_points = stats.get("total_points", 0)
            count += 1

        self.db.flush()
        return count

    def _sync_all_dream_teams(self) -> int:
        """Sync dream teams for all finished gameweeks."""
        finished_gws = (
            self.db.query(Gameweek).filter(Gameweek.finished == True).all()  # noqa: E712
        )
        logger.info(f"Syncing dream teams for {len(finished_gws)} finished gameweeks")

        total_count = 0
        for gw in finished_gws:
            count = self._sync_dream_team(gw.fpl_id)
            total_count += count

        return total_count

    def _sync_dream_team(self, gw_fpl_id: int) -> int:
        """Sync dream team for a single gameweek."""
        try:
            dream_team_data = self.fpl_client.get_dream_team(gw_fpl_id)
        except Exception as e:
            logger.warning(f"Failed to fetch dream team for GW {gw_fpl_id}: {e}")
            return 0

        team_list = dream_team_data.get("team", [])
        if not team_list:
            return 0

        # Build mappings
        players = self.db.query(Player).all()
        player_map = {p.fpl_id: p.id for p in players}
        gw = self.db.query(Gameweek).filter(Gameweek.fpl_id == gw_fpl_id).first()
        if not gw:
            return 0

        count = 0
        for idx, entry in enumerate(team_list, start=1):
            player_fpl_id = entry["element"]
            player_db_id = player_map.get(player_fpl_id)
            if not player_db_id:
                continue

            # Check if entry already exists
            existing = (
                self.db.query(DreamTeam)
                .filter(
                    DreamTeam.gameweek_id == gw.id,
                    DreamTeam.player_id == player_db_id,
                )
                .first()
            )

            if not existing:
                existing = DreamTeam(gameweek_id=gw.id, player_id=player_db_id)
                self.db.add(existing)

            existing.position_slot = idx
            existing.points = entry.get("points", 0)
            count += 1

        self.db.flush()
        return count

    def _sync_set_piece_takers(self) -> None:
        """Sync set piece taker information."""
        try:
            set_piece_data = self.fpl_client.get_set_piece_notes()
        except Exception as e:
            logger.warning(f"Failed to fetch set piece notes: {e}")
            return

        # Reset all set piece flags first
        self.db.query(Player).update(
            {
                Player.is_penalty_taker: False,
                Player.is_corner_taker: False,
                Player.is_freekick_taker: False,
            }
        )

        # The set piece notes API returns team-level notes as text
        # We'd need to parse these or use a different approach
        # For now, this is a placeholder - the actual implementation
        # would parse the notes text to identify takers
        logger.info("Set piece taker sync placeholder - manual mapping may be needed")
        self.db.flush()


def sync_fpl_data(db: Session) -> dict[str, int]:
    """Convenience function to sync all FPL data."""
    with DataIngestionService(db) as service:
        return service.sync_all()
