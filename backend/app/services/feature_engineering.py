"""Feature engineering for player predictions."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.constants import (
    MIN_GAMEWEEKS_FOR_PREDICTION,
    ROLLING_WINDOWS,
    Position,
    PointsSystem,
)
from app.models import Fixture, Gameweek, Player, PlayerGWStats, Team

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Generates features for ML models from player stats."""

    def __init__(self, db: Session):
        self.db = db

    def get_player_features_for_gameweek(
        self, target_gw: int
    ) -> pd.DataFrame:
        """
        Generate features for all players for a specific gameweek prediction.

        Args:
            target_gw: The gameweek to predict for (uses data before this GW)

        Returns:
            DataFrame with one row per player and feature columns
        """
        # Get all players
        players = self.db.query(Player).all()
        gameweeks = self.db.query(Gameweek).filter(Gameweek.fpl_id < target_gw).all()
        gw_ids = [gw.id for gw in gameweeks]

        if len(gw_ids) < MIN_GAMEWEEKS_FOR_PREDICTION:
            logger.warning(
                f"Not enough gameweeks ({len(gw_ids)}) for feature engineering"
            )
            return pd.DataFrame()

        # Get all player stats for historical gameweeks
        stats = (
            self.db.query(PlayerGWStats)
            .filter(PlayerGWStats.gameweek_id.in_(gw_ids))
            .all()
        )

        # Build player stats DataFrame
        stats_data = []
        for s in stats:
            gw = next((g for g in gameweeks if g.id == s.gameweek_id), None)
            if gw:
                stats_data.append(
                    {
                        "player_id": s.player_id,
                        "gw_fpl_id": gw.fpl_id,
                        "minutes": s.minutes,
                        "goals_scored": s.goals_scored,
                        "assists": s.assists,
                        "clean_sheets": s.clean_sheets,
                        "goals_conceded": s.goals_conceded,
                        "saves": s.saves,
                        "bonus": s.bonus,
                        "bps": s.bps,
                        "total_points": s.total_points,
                        "shots": s.shots or 0,
                        "key_passes": s.key_passes or 0,
                        "xg": float(s.xg) if s.xg else 0.0,
                        "xa": float(s.xa) if s.xa else 0.0,
                    }
                )

        if not stats_data:
            return pd.DataFrame()

        stats_df = pd.DataFrame(stats_data)
        stats_df = stats_df.sort_values(["player_id", "gw_fpl_id"])

        # Get fixture info for target gameweek
        target_gw_db = (
            self.db.query(Gameweek).filter(Gameweek.fpl_id == target_gw).first()
        )
        fixtures = []
        if target_gw_db:
            fixtures = (
                self.db.query(Fixture)
                .filter(Fixture.gameweek_id == target_gw_db.id)
                .all()
            )

        # Build fixture mapping: team_id -> (opponent_id, is_home, difficulty)
        fixture_map = {}
        teams = self.db.query(Team).all()
        team_db_to_fpl = {t.id: t.fpl_id for t in teams}

        for fix in fixtures:
            fixture_map[fix.team_home_id] = {
                "opponent_id": fix.team_away_id,
                "is_home": True,
                "difficulty": fix.difficulty_home or 3,
            }
            fixture_map[fix.team_away_id] = {
                "opponent_id": fix.team_home_id,
                "is_home": False,
                "difficulty": fix.difficulty_away or 3,
            }

        # Generate features per player
        features = []
        for player in players:
            player_stats = stats_df[stats_df["player_id"] == player.id]

            if len(player_stats) == 0:
                # New player or no appearances
                continue

            feature_row = self._compute_player_features(
                player, player_stats, fixture_map, teams
            )
            if feature_row:
                features.append(feature_row)

        return pd.DataFrame(features)

    def _compute_player_features(
        self,
        player: Player,
        stats_df: pd.DataFrame,
        fixture_map: dict[int, dict[str, Any]],
        teams: list[Team],
    ) -> dict[str, Any] | None:
        """Compute features for a single player."""
        if len(stats_df) == 0:
            return None

        # Get team info
        team = next((t for t in teams if t.id == player.team_id), None)
        fixture_info = fixture_map.get(player.team_id, {})

        features: dict[str, Any] = {
            "player_id": player.id,
            "player_fpl_id": player.fpl_id,
            "position": player.position,
            "team_id": player.team_id,
        }

        # Position encoding
        features["is_gkp"] = 1 if player.position == Position.GKP.value else 0
        features["is_def"] = 1 if player.position == Position.DEF.value else 0
        features["is_mid"] = 1 if player.position == Position.MID.value else 0
        features["is_fwd"] = 1 if player.position == Position.FWD.value else 0

        # Set piece duties
        features["is_penalty_taker"] = 1 if player.is_penalty_taker else 0
        features["is_set_piece_taker"] = (
            1 if (player.is_corner_taker or player.is_freekick_taker) else 0
        )

        # Current state
        features["now_cost"] = player.now_cost or 50
        features["chance_of_playing"] = player.chance_of_playing or 100

        # Rolling stats for different windows
        for window in ROLLING_WINDOWS:
            recent_stats = stats_df.tail(window)

            # Basic rolling stats
            features[f"points_mean_{window}"] = recent_stats["total_points"].mean()
            features[f"points_sum_{window}"] = recent_stats["total_points"].sum()
            features[f"points_std_{window}"] = recent_stats["total_points"].std() or 0

            features[f"minutes_mean_{window}"] = recent_stats["minutes"].mean()
            features[f"starts_{window}"] = (recent_stats["minutes"] >= 60).sum()

            features[f"goals_sum_{window}"] = recent_stats["goals_scored"].sum()
            features[f"assists_sum_{window}"] = recent_stats["assists"].sum()
            features[f"ga_sum_{window}"] = (
                recent_stats["goals_scored"].sum() + recent_stats["assists"].sum()
            )

            features[f"cs_sum_{window}"] = recent_stats["clean_sheets"].sum()
            features[f"bonus_sum_{window}"] = recent_stats["bonus"].sum()
            features[f"bps_mean_{window}"] = recent_stats["bps"].mean()

            # xG/xA if available
            features[f"xg_sum_{window}"] = recent_stats["xg"].sum()
            features[f"xa_sum_{window}"] = recent_stats["xa"].sum()
            features[f"xga_sum_{window}"] = (
                recent_stats["xg"].sum() + recent_stats["xa"].sum()
            )

            # Goal-xG overperformance
            goals = recent_stats["goals_scored"].sum()
            xg = recent_stats["xg"].sum()
            features[f"goal_overperformance_{window}"] = goals - xg if xg > 0 else 0

            # Involvement (shots + key passes)
            features[f"involvement_{window}"] = (
                recent_stats["shots"].sum() + recent_stats["key_passes"].sum()
            )

        # Fixture context
        features["is_home"] = 1 if fixture_info.get("is_home", False) else 0
        features["fixture_difficulty"] = fixture_info.get("difficulty", 3)

        # Opponent strength
        opponent_id = fixture_info.get("opponent_id")
        if opponent_id:
            opponent = next((t for t in teams if t.id == opponent_id), None)
            if opponent:
                if features["is_home"]:
                    features["opponent_attack_strength"] = (
                        opponent.strength_attack_away or 1000
                    )
                    features["opponent_defence_strength"] = (
                        opponent.strength_defence_away or 1000
                    )
                else:
                    features["opponent_attack_strength"] = (
                        opponent.strength_attack_home or 1000
                    )
                    features["opponent_defence_strength"] = (
                        opponent.strength_defence_home or 1000
                    )
            else:
                features["opponent_attack_strength"] = 1000
                features["opponent_defence_strength"] = 1000
        else:
            features["opponent_attack_strength"] = 1000
            features["opponent_defence_strength"] = 1000

        # Team strength
        if team:
            if features["is_home"]:
                features["team_attack_strength"] = team.strength_attack_home or 1000
                features["team_defence_strength"] = team.strength_defence_home or 1000
            else:
                features["team_attack_strength"] = team.strength_attack_away or 1000
                features["team_defence_strength"] = team.strength_defence_away or 1000
        else:
            features["team_attack_strength"] = 1000
            features["team_defence_strength"] = 1000

        # Games played (for filtering)
        features["games_played"] = len(stats_df)

        return features

    def get_training_data(
        self, min_gw: int, max_gw: int
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Get features and targets for training.

        Args:
            min_gw: Minimum gameweek to include
            max_gw: Maximum gameweek to include

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        all_features = []
        all_targets = []

        for gw in range(min_gw, max_gw + 1):
            # Get features using data before this GW
            features_df = self.get_player_features_for_gameweek(gw)
            if features_df.empty:
                continue

            # Get actual points for this GW
            gw_db = self.db.query(Gameweek).filter(Gameweek.fpl_id == gw).first()
            if not gw_db:
                continue

            stats = (
                self.db.query(PlayerGWStats)
                .filter(PlayerGWStats.gameweek_id == gw_db.id)
                .all()
            )
            actual_points = {s.player_id: s.total_points for s in stats}

            # Add target column
            features_df["target_points"] = features_df["player_id"].map(
                lambda x: actual_points.get(x, 0)
            )
            features_df["target_gw"] = gw

            all_features.append(features_df)

        if not all_features:
            return pd.DataFrame(), pd.Series()

        combined = pd.concat(all_features, ignore_index=True)
        targets = combined["target_points"]
        features = combined.drop(columns=["target_points", "target_gw"])

        return features, targets
