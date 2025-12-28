"""Initial schema - all tables for FPL TOTW predictor.

Revision ID: 001_initial
Revises:
Create Date: 2024-12-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    # Teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fpl_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("short_name", sa.String(length=10), nullable=True),
        sa.Column("strength_attack_home", sa.Integer(), nullable=True),
        sa.Column("strength_attack_away", sa.Integer(), nullable=True),
        sa.Column("strength_defence_home", sa.Integer(), nullable=True),
        sa.Column("strength_defence_away", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_fpl_id", "teams", ["fpl_id"], unique=True)

    # Gameweeks table
    op.create_table(
        "gameweeks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fpl_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=True),
        sa.Column("finished", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_next", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gameweeks_fpl_id", "gameweeks", ["fpl_id"], unique=True)

    # Players table
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fpl_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("understat_id", sa.Integer(), nullable=True),
        sa.Column("web_name", sa.String(length=100), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("second_name", sa.String(length=100), nullable=True),
        sa.Column("position", sa.String(length=10), nullable=False),
        sa.Column("now_cost", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("chance_of_playing", sa.Integer(), nullable=True),
        sa.Column("news", sa.Text(), nullable=True),
        sa.Column(
            "is_penalty_taker", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_corner_taker", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_freekick_taker", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_players_fpl_id", "players", ["fpl_id"], unique=True)

    # Fixtures table
    op.create_table(
        "fixtures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fpl_id", sa.Integer(), nullable=False),
        sa.Column("gameweek_id", sa.Integer(), nullable=True),
        sa.Column("team_home_id", sa.Integer(), nullable=False),
        sa.Column("team_away_id", sa.Integer(), nullable=False),
        sa.Column("kickoff_time", sa.DateTime(), nullable=True),
        sa.Column("difficulty_home", sa.Integer(), nullable=True),
        sa.Column("difficulty_away", sa.Integer(), nullable=True),
        sa.Column("team_h_score", sa.Integer(), nullable=True),
        sa.Column("team_a_score", sa.Integer(), nullable=True),
        sa.Column("finished", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["gameweek_id"], ["gameweeks.id"]),
        sa.ForeignKeyConstraint(["team_home_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["team_away_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fixtures_fpl_id", "fixtures", ["fpl_id"], unique=True)

    # Player GW Stats table
    op.create_table(
        "player_gw_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("gameweek_id", sa.Integer(), nullable=False),
        sa.Column("fixture_id", sa.Integer(), nullable=True),
        sa.Column("minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals_scored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clean_sheets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals_conceded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("own_goals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalties_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalties_missed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yellow_cards", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("red_cards", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("key_passes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xg", sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column("xa", sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column("npxg", sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.ForeignKeyConstraint(["fixture_id"], ["fixtures.id"]),
        sa.ForeignKeyConstraint(["gameweek_id"], ["gameweeks.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "gameweek_id", name="uq_player_gameweek"),
    )
    op.create_index("ix_player_gw_stats_player_id", "player_gw_stats", ["player_id"])
    op.create_index(
        "ix_player_gw_stats_gameweek_id", "player_gw_stats", ["gameweek_id"]
    )

    # Dream Teams table (ground truth)
    op.create_table(
        "dream_teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gameweek_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position_slot", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["gameweek_id"], ["gameweeks.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "gameweek_id", "player_id", name="uq_dream_team_gw_player"
        ),
    )
    op.create_index("ix_dream_teams_gameweek_id", "dream_teams", ["gameweek_id"])
    op.create_index("ix_dream_teams_player_id", "dream_teams", ["player_id"])

    # Predictions table
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gameweek_id", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("total_predicted_points", sa.Integer(), nullable=True),
        sa.Column("formation", sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(["gameweek_id"], ["gameweeks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_gameweek_id", "predictions", ["gameweek_id"])

    # Prediction Players table
    op.create_table(
        "prediction_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position_slot", sa.Integer(), nullable=False),
        sa.Column(
            "predicted_points", sa.DECIMAL(precision=5, scale=2), nullable=False
        ),
        sa.Column(
            "predicted_minutes", sa.DECIMAL(precision=5, scale=2), nullable=True
        ),
        sa.Column("start_probability", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column("confidence", sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["prediction_id"], ["predictions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prediction_players_prediction_id", "prediction_players", ["prediction_id"]
    )
    op.create_index(
        "ix_prediction_players_player_id", "prediction_players", ["player_id"]
    )

    # Backtest Results table
    op.create_table(
        "backtest_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gameweek_id", sa.Integer(), nullable=False),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("player_overlap", sa.Integer(), nullable=False),
        sa.Column("points_ratio", sa.DECIMAL(precision=5, scale=4), nullable=False),
        sa.Column("actual_total", sa.Integer(), nullable=False),
        sa.Column("predicted_total", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["gameweek_id"], ["gameweeks.id"]),
        sa.ForeignKeyConstraint(["prediction_id"], ["predictions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prediction_id"),
    )
    op.create_index(
        "ix_backtest_results_gameweek_id", "backtest_results", ["gameweek_id"]
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("backtest_results")
    op.drop_table("prediction_players")
    op.drop_table("predictions")
    op.drop_table("dream_teams")
    op.drop_table("player_gw_stats")
    op.drop_table("fixtures")
    op.drop_table("players")
    op.drop_table("gameweeks")
    op.drop_table("teams")
