"""
Application constants and enums.

Constants are loaded from the shared JSON file (shared/constants.json)
to ensure consistency between Python backend and TypeScript frontend.
"""

import json
from enum import Enum
from pathlib import Path

# Load shared constants from JSON
# Path: backend/app/constants.py -> backend/app -> backend -> fpl_totw -> shared/constants.json
_SHARED_CONSTANTS_PATH = Path(__file__).parent.parent.parent / "shared" / "constants.json"

with open(_SHARED_CONSTANTS_PATH, "r") as f:
    _SHARED = json.load(f)


class Position(str, Enum):
    """Player positions in FPL - values from shared constants."""

    GKP = _SHARED["positions"]["GKP"]
    DEF = _SHARED["positions"]["DEF"]
    MID = _SHARED["positions"]["MID"]
    FWD = _SHARED["positions"]["FWD"]

    @classmethod
    def from_element_type(cls, element_type: int) -> "Position":
        """Convert FPL element_type (1-4) to Position enum."""
        mapping = _SHARED["positionElementTypeMap"]
        position_str = mapping.get(str(element_type), "MID")
        return cls(position_str)


class PlayerStatus(str, Enum):
    """Player availability status codes from FPL - values from shared constants."""

    AVAILABLE = _SHARED["playerStatus"]["AVAILABLE"]
    DOUBTFUL = _SHARED["playerStatus"]["DOUBTFUL"]
    INJURED = _SHARED["playerStatus"]["INJURED"]
    NOT_AVAILABLE = _SHARED["playerStatus"]["NOT_AVAILABLE"]
    SUSPENDED = _SHARED["playerStatus"]["SUSPENDED"]
    UNAVAILABLE = _SHARED["playerStatus"]["UNAVAILABLE"]


class Formation(str, Enum):
    """Valid Dream Team formations - values from shared constants."""

    F_3_4_3 = _SHARED["formations"][0]
    F_3_5_2 = _SHARED["formations"][1]
    F_4_3_3 = _SHARED["formations"][2]
    F_4_4_2 = _SHARED["formations"][3]
    F_4_5_1 = _SHARED["formations"][4]
    F_5_3_2 = _SHARED["formations"][5]
    F_5_4_1 = _SHARED["formations"][6]


# Formation constraints loaded from shared constants
FORMATION_CONSTRAINTS = {
    "min_gkp": _SHARED["formationConstraints"]["minGkp"],
    "max_gkp": _SHARED["formationConstraints"]["maxGkp"],
    "min_def": _SHARED["formationConstraints"]["minDef"],
    "max_def": _SHARED["formationConstraints"]["maxDef"],
    "min_mid": _SHARED["formationConstraints"]["minMid"],
    "max_mid": _SHARED["formationConstraints"]["maxMid"],
    "min_fwd": _SHARED["formationConstraints"]["minFwd"],
    "max_fwd": _SHARED["formationConstraints"]["maxFwd"],
    "total_players": _SHARED["formationConstraints"]["totalPlayers"],
}


class PointsSystem:
    """FPL points awarded for various actions - values from shared constants."""

    # Load from shared
    _ps = _SHARED["pointsSystem"]

    # Appearance
    MINUTES_1_TO_59: int = _ps["minutes1To59"]
    MINUTES_60_PLUS: int = _ps["minutes60Plus"]

    # Goals
    GOAL_GKP: int = _ps["goalGkp"]
    GOAL_DEF: int = _ps["goalDef"]
    GOAL_MID: int = _ps["goalMid"]
    GOAL_FWD: int = _ps["goalFwd"]

    # Assists
    ASSIST: int = _ps["assist"]

    # Clean sheets
    CLEAN_SHEET_GKP: int = _ps["cleanSheetGkp"]
    CLEAN_SHEET_DEF: int = _ps["cleanSheetDef"]
    CLEAN_SHEET_MID: int = _ps["cleanSheetMid"]
    CLEAN_SHEET_FWD: int = _ps["cleanSheetFwd"]

    # Goals conceded (per 2)
    GOALS_CONCEDED_GKP: int = _ps["goalsConcededGkp"]
    GOALS_CONCEDED_DEF: int = _ps["goalsConcededDef"]

    # Saves (GK only, per 3)
    SAVES_BONUS: int = _ps["savesBonus"]

    # Penalties
    PENALTY_SAVED: int = _ps["penaltySaved"]
    PENALTY_MISSED: int = _ps["penaltyMissed"]

    # Cards
    YELLOW_CARD: int = _ps["yellowCard"]
    RED_CARD: int = _ps["redCard"]

    # Own goals
    OWN_GOAL: int = _ps["ownGoal"]

    # Bonus points
    MAX_BONUS: int = _ps["maxBonus"]

    @classmethod
    def goal_points(cls, position: Position) -> int:
        """Get goal points for a position."""
        mapping = {
            Position.GKP: cls.GOAL_GKP,
            Position.DEF: cls.GOAL_DEF,
            Position.MID: cls.GOAL_MID,
            Position.FWD: cls.GOAL_FWD,
        }
        return mapping.get(position, cls.GOAL_FWD)

    @classmethod
    def clean_sheet_points(cls, position: Position) -> int:
        """Get clean sheet points for a position."""
        mapping = {
            Position.GKP: cls.CLEAN_SHEET_GKP,
            Position.DEF: cls.CLEAN_SHEET_DEF,
            Position.MID: cls.CLEAN_SHEET_MID,
            Position.FWD: cls.CLEAN_SHEET_FWD,
        }
        return mapping.get(position, 0)


# Rolling window sizes for feature engineering - from shared constants
ROLLING_WINDOWS: list[int] = _SHARED["rollingWindows"]

# Minimum gameweeks required for predictions - from shared constants
MIN_GAMEWEEKS_FOR_PREDICTION: int = _SHARED["minGameweeksForPrediction"]

# API rate limiting - from shared constants
FPL_API_RATE_LIMIT_SECONDS: float = _SHARED["apiRateLimitSeconds"]

# FPL API base URL - from shared constants
FPL_API_BASE_URL: str = _SHARED["fplApiBaseUrl"]

# Model hyperparameters (backend-only, not shared)
# Note: num_leaves should be <= 2^max_depth to avoid LightGBM warning
DEFAULT_MODEL_PARAMS = {
    "lightgbm": {
        "n_estimators": 200,
        "max_depth": 5,
        "learning_rate": 0.05,
        "num_leaves": 20,  # <= 2^5 = 32
        "min_child_samples": 10,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
        "verbosity": -1,  # Suppress warnings
    }
}

# Cache TTLs (backend-only, not shared)
CACHE_TTL_BOOTSTRAP = 3600  # 1 hour
CACHE_TTL_LIVE = 60  # 1 minute
