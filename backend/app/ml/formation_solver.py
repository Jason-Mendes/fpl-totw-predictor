"""Formation solver to select optimal XI from predicted points."""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

from app.constants import FORMATION_CONSTRAINTS, Position

logger = logging.getLogger(__name__)


@dataclass
class PlayerPrediction:
    """Prediction for a single player."""

    player_id: int
    player_fpl_id: int
    position: str
    predicted_points: float
    web_name: str = ""


def solve_formation(
    predictions: list[PlayerPrediction],
) -> tuple[list[PlayerPrediction], str]:
    """
    Select optimal XI from player predictions using integer linear programming.

    Constraints:
    - Exactly 1 GKP
    - 3-5 DEF
    - 2-5 MID
    - 1-3 FWD
    - Exactly 11 players total

    Args:
        predictions: List of player predictions

    Returns:
        Tuple of (selected XI, formation string like "4-5-1")
    """
    if len(predictions) < 11:
        logger.warning(f"Only {len(predictions)} players available, need at least 11")
        return predictions[:11] if predictions else [], "N/A"

    n = len(predictions)

    # Group by position
    gkp_idx = [i for i, p in enumerate(predictions) if p.position == Position.GKP.value]
    def_idx = [i for i, p in enumerate(predictions) if p.position == Position.DEF.value]
    mid_idx = [i for i, p in enumerate(predictions) if p.position == Position.MID.value]
    fwd_idx = [i for i, p in enumerate(predictions) if p.position == Position.FWD.value]

    # Check if we have enough players
    if len(gkp_idx) < 1:
        logger.error("No goalkeepers available")
        return [], "N/A"
    if len(def_idx) < FORMATION_CONSTRAINTS["min_def"]:
        logger.error(f"Only {len(def_idx)} defenders available, need at least {FORMATION_CONSTRAINTS['min_def']}")
        return [], "N/A"
    if len(mid_idx) < FORMATION_CONSTRAINTS["min_mid"]:
        logger.error(f"Only {len(mid_idx)} midfielders available, need at least {FORMATION_CONSTRAINTS['min_mid']}")
        return [], "N/A"
    if len(fwd_idx) < FORMATION_CONSTRAINTS["min_fwd"]:
        logger.error(f"Only {len(fwd_idx)} forwards available, need at least {FORMATION_CONSTRAINTS['min_fwd']}")
        return [], "N/A"

    # Objective: maximize predicted points (negative for minimization)
    c = np.array([-p.predicted_points for p in predictions])

    # Constraints matrix
    constraints = []

    # Total players = 11
    A_total = np.ones(n)
    constraints.append(LinearConstraint(A_total, 11, 11))

    # GKP = 1
    A_gkp = np.zeros(n)
    for i in gkp_idx:
        A_gkp[i] = 1
    constraints.append(LinearConstraint(A_gkp, 1, 1))

    # DEF: 3-5
    A_def = np.zeros(n)
    for i in def_idx:
        A_def[i] = 1
    constraints.append(
        LinearConstraint(
            A_def,
            FORMATION_CONSTRAINTS["min_def"],
            FORMATION_CONSTRAINTS["max_def"],
        )
    )

    # MID: 2-5
    A_mid = np.zeros(n)
    for i in mid_idx:
        A_mid[i] = 1
    constraints.append(
        LinearConstraint(
            A_mid,
            FORMATION_CONSTRAINTS["min_mid"],
            FORMATION_CONSTRAINTS["max_mid"],
        )
    )

    # FWD: 1-3
    A_fwd = np.zeros(n)
    for i in fwd_idx:
        A_fwd[i] = 1
    constraints.append(
        LinearConstraint(
            A_fwd,
            FORMATION_CONSTRAINTS["min_fwd"],
            FORMATION_CONSTRAINTS["max_fwd"],
        )
    )

    # Bounds: binary variables (0 or 1)
    bounds = Bounds(lb=np.zeros(n), ub=np.ones(n))

    # Solve as integer program
    try:
        result = milp(
            c=c,
            constraints=constraints,
            bounds=bounds,
            integrality=np.ones(n),  # All variables are integers
        )

        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
            return _fallback_selection(predictions), "N/A"

        # Extract selected players
        selected_idx = np.where(result.x > 0.5)[0]
        selected = [predictions[i] for i in selected_idx]

        # Determine formation
        n_def = sum(1 for p in selected if p.position == Position.DEF.value)
        n_mid = sum(1 for p in selected if p.position == Position.MID.value)
        n_fwd = sum(1 for p in selected if p.position == Position.FWD.value)
        formation = f"{n_def}-{n_mid}-{n_fwd}"

        # Sort by position for display
        position_order = {
            Position.GKP.value: 0,
            Position.DEF.value: 1,
            Position.MID.value: 2,
            Position.FWD.value: 3,
        }
        selected.sort(key=lambda p: (position_order.get(p.position, 4), -p.predicted_points))

        return selected, formation

    except Exception as e:
        logger.error(f"Formation solver error: {e}")
        return _fallback_selection(predictions), "N/A"


def _fallback_selection(predictions: list[PlayerPrediction]) -> list[PlayerPrediction]:
    """Fallback greedy selection if optimization fails."""
    by_position = {
        Position.GKP.value: [],
        Position.DEF.value: [],
        Position.MID.value: [],
        Position.FWD.value: [],
    }

    for p in predictions:
        if p.position in by_position:
            by_position[p.position].append(p)

    # Sort each by predicted points
    for pos in by_position:
        by_position[pos].sort(key=lambda x: -x.predicted_points)

    # Select greedily: 1 GK, 4 DEF, 4 MID, 2 FWD (4-4-2)
    selected = []
    selected.extend(by_position[Position.GKP.value][:1])
    selected.extend(by_position[Position.DEF.value][:4])
    selected.extend(by_position[Position.MID.value][:4])
    selected.extend(by_position[Position.FWD.value][:2])

    return selected
