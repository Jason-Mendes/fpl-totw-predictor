"""Simple baseline model using weighted rolling form.

This model serves as a sanity check - if the complex ML model can't beat
weighted form averages, something is wrong with the training.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.constants import Position

logger = logging.getLogger(__name__)


class SimpleFormPredictor:
    """
    Simple predictor that uses weighted rolling averages.

    Prediction formula:
        predicted_points = (
            0.4 * points_mean_3 +
            0.35 * points_mean_5 +
            0.25 * points_mean_8
        ) * fixture_modifier

    Where fixture_modifier adjusts for:
    - Home advantage: +10%
    - Easy fixture (difficulty 1-2): +10%
    - Hard fixture (difficulty 4-5): -10%
    """

    def __init__(
        self,
        weight_3: float = 0.4,
        weight_5: float = 0.35,
        weight_8: float = 0.25,
        home_bonus: float = 0.10,
        easy_fixture_bonus: float = 0.10,
        hard_fixture_penalty: float = 0.10,
    ):
        self.weight_3 = weight_3
        self.weight_5 = weight_5
        self.weight_8 = weight_8
        self.home_bonus = home_bonus
        self.easy_fixture_bonus = easy_fixture_bonus
        self.hard_fixture_penalty = hard_fixture_penalty

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict points using weighted form averages.

        Args:
            X: Feature DataFrame with columns:
               - points_mean_3, points_mean_5, points_mean_8
               - is_home, fixture_difficulty

        Returns:
            Array of predicted points
        """
        predictions = []

        for _, row in X.iterrows():
            # Base prediction from weighted form
            base_pred = (
                self.weight_3 * row.get("points_mean_3", 0)
                + self.weight_5 * row.get("points_mean_5", 0)
                + self.weight_8 * row.get("points_mean_8", 0)
            )

            # Calculate fixture modifier
            modifier = 1.0

            # Home advantage
            if row.get("is_home", 0) == 1:
                modifier += self.home_bonus

            # Fixture difficulty adjustment
            difficulty = row.get("fixture_difficulty", 3)
            if difficulty <= 2:
                modifier += self.easy_fixture_bonus
            elif difficulty >= 4:
                modifier -= self.hard_fixture_penalty

            # Apply modifier
            pred = base_pred * modifier

            # Minimum 0 points
            predictions.append(max(0, pred))

        return np.array(predictions)

    def get_params(self) -> dict[str, Any]:
        """Get model parameters."""
        return {
            "weight_3": self.weight_3,
            "weight_5": self.weight_5,
            "weight_8": self.weight_8,
            "home_bonus": self.home_bonus,
            "easy_fixture_bonus": self.easy_fixture_bonus,
            "hard_fixture_penalty": self.hard_fixture_penalty,
        }


def compare_models(
    X: pd.DataFrame,
    y: pd.Series,
    lgbm_predictions: np.ndarray,
) -> dict[str, Any]:
    """
    Compare LightGBM predictions against simple baseline.

    Args:
        X: Feature DataFrame
        y: Actual points
        lgbm_predictions: Predictions from LightGBM model

    Returns:
        Comparison metrics
    """
    simple_model = SimpleFormPredictor()
    simple_predictions = simple_model.predict(X)

    # Calculate MAE for both
    lgbm_mae = np.mean(np.abs(lgbm_predictions - y))
    simple_mae = np.mean(np.abs(simple_predictions - y))

    # Calculate top-11 overlap (the metric that matters for TOTW)
    # Sort by predictions and get top 11
    lgbm_top11_idx = np.argsort(lgbm_predictions)[-11:]
    simple_top11_idx = np.argsort(simple_predictions)[-11:]
    actual_top11_idx = np.argsort(y.values)[-11:]

    lgbm_overlap = len(set(lgbm_top11_idx) & set(actual_top11_idx))
    simple_overlap = len(set(simple_top11_idx) & set(actual_top11_idx))

    return {
        "lgbm_mae": lgbm_mae,
        "simple_mae": simple_mae,
        "lgbm_top11_overlap": lgbm_overlap,
        "simple_top11_overlap": simple_overlap,
        "simple_beats_lgbm_mae": simple_mae < lgbm_mae,
        "simple_beats_lgbm_overlap": simple_overlap > lgbm_overlap,
    }
