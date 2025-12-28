"""Pydantic schemas for API request/response models."""

from datetime import datetime

from pydantic import BaseModel


class TeamSchema(BaseModel):
    """Team schema."""

    id: int
    fpl_id: int
    name: str
    short_name: str | None
    strength_attack_home: int | None
    strength_attack_away: int | None
    strength_defence_home: int | None
    strength_defence_away: int | None

    class Config:
        from_attributes = True


class PlayerSchema(BaseModel):
    """Player schema."""

    id: int
    fpl_id: int
    web_name: str
    first_name: str | None
    second_name: str | None
    position: str
    team_id: int | None
    team_name: str | None = None
    team_short_name: str | None = None
    now_cost: int | None
    status: str | None
    chance_of_playing: int | None
    is_penalty_taker: bool
    is_corner_taker: bool
    is_freekick_taker: bool

    class Config:
        from_attributes = True


class GameweekSchema(BaseModel):
    """Gameweek schema."""

    id: int
    fpl_id: int
    name: str | None
    deadline: datetime | None
    finished: bool
    is_current: bool
    is_next: bool

    class Config:
        from_attributes = True


class FixtureSchema(BaseModel):
    """Fixture schema."""

    id: int
    fpl_id: int
    gameweek_id: int | None
    team_home_id: int
    team_away_id: int
    team_home_name: str | None = None
    team_away_name: str | None = None
    kickoff_time: datetime | None
    difficulty_home: int | None
    difficulty_away: int | None
    team_h_score: int | None
    team_a_score: int | None
    finished: bool

    class Config:
        from_attributes = True


class PlayerStatsSchema(BaseModel):
    """Player gameweek stats schema."""

    id: int
    player_id: int
    gameweek_id: int
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int
    bps: int
    total_points: int
    xg: float | None
    xa: float | None
    npxg: float | None

    class Config:
        from_attributes = True


class DreamTeamPlayerSchema(BaseModel):
    """Individual player in dream team."""

    player_id: int
    player_fpl_id: int
    web_name: str
    position: str
    team_short_name: str | None
    team_fpl_id: int | None
    position_slot: int
    points: int

    class Config:
        from_attributes = True


class DreamTeamSchema(BaseModel):
    """Dream team for a gameweek."""

    gameweek_id: int
    gameweek_fpl_id: int
    total_points: int
    players: list[DreamTeamPlayerSchema]

    class Config:
        from_attributes = True


class PredictionPlayerSchema(BaseModel):
    """Individual player in a prediction."""

    player_id: int
    player_fpl_id: int
    web_name: str
    position: str
    team_short_name: str | None
    team_fpl_id: int | None
    position_slot: int
    predicted_points: float
    predicted_minutes: float | None
    start_probability: float | None
    confidence: float | None

    class Config:
        from_attributes = True


class PredictionSchema(BaseModel):
    """Prediction for a gameweek."""

    id: int
    gameweek_id: int
    gameweek_fpl_id: int
    model_version: str | None
    created_at: datetime
    total_predicted_points: int | None
    formation: str | None
    players: list[PredictionPlayerSchema]

    class Config:
        from_attributes = True


class BacktestResultSchema(BaseModel):
    """Backtest result for a single gameweek."""

    gameweek_id: int
    gameweek_fpl_id: int
    player_overlap: int
    points_ratio: float
    actual_total: int  # Dream team's actual points
    predicted_total: int  # Our predicted points for our team
    predicted_team_actual: int | None = None  # Actual points scored by our predicted players
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestSummarySchema(BaseModel):
    """Summary of backtest results."""

    total_gameweeks: int
    avg_overlap: float
    avg_points_ratio: float
    avg_predicted_team_actual: float | None = None  # Avg actual points by our predicted team
    avg_dream_team_points: float | None = None  # Avg dream team points for comparison
    min_overlap: int
    max_overlap: int
    weeks_above_9: int
    weeks_above_8: int
    results: list[BacktestResultSchema]


class SyncResultSchema(BaseModel):
    """Result of data sync operation."""

    teams: int
    gameweeks: int
    players: int
    fixtures: int
    player_stats: int
    dream_teams: int
