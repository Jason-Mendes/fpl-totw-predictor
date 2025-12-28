"""Points prediction model using LightGBM."""

import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

from app.constants import DEFAULT_MODEL_PARAMS, Position

logger = logging.getLogger(__name__)

# Features to use for training (excluding identifiers)
# NOTE: now_cost removed - it caused the model to penalize expensive players
# (high feature importance but learned inverse relationship due to class imbalance)
FEATURE_COLUMNS = [
    "is_gkp",
    "is_def",
    "is_mid",
    "is_fwd",
    "is_penalty_taker",
    "is_set_piece_taker",
    # "now_cost",  # Removed - caused model to favor cheap players incorrectly
    "chance_of_playing",
    # Rolling window features for window 3
    "points_mean_3",
    "points_sum_3",
    "points_std_3",
    "minutes_mean_3",
    "starts_3",
    "goals_sum_3",
    "assists_sum_3",
    "ga_sum_3",
    "cs_sum_3",
    "bonus_sum_3",
    "bps_mean_3",
    # xG features - now enabled after Understat sync
    "xg_sum_3",
    "xa_sum_3",
    "xga_sum_3",
    "goal_overperformance_3",
    "involvement_3",
    # Rolling window features for window 5
    "points_mean_5",
    "points_sum_5",
    "points_std_5",
    "minutes_mean_5",
    "starts_5",
    "goals_sum_5",
    "assists_sum_5",
    "ga_sum_5",
    "cs_sum_5",
    "bonus_sum_5",
    "bps_mean_5",
    "xg_sum_5",
    "xa_sum_5",
    "xga_sum_5",
    "goal_overperformance_5",
    "involvement_5",
    # Rolling window features for window 8
    "points_mean_8",
    "points_sum_8",
    "points_std_8",
    "minutes_mean_8",
    "starts_8",
    "goals_sum_8",
    "assists_sum_8",
    "ga_sum_8",
    "cs_sum_8",
    "bonus_sum_8",
    "bps_mean_8",
    "xg_sum_8",
    "xa_sum_8",
    "xga_sum_8",
    "goal_overperformance_8",
    "involvement_8",
    # Fixture context
    "is_home",
    "fixture_difficulty",
    "opponent_attack_strength",
    "opponent_defence_strength",
    "team_attack_strength",
    "team_defence_strength",
    "games_played",
]


class PointsPredictor:
    """LightGBM model to predict FPL points."""

    def __init__(self):
        params = DEFAULT_MODEL_PARAMS["lightgbm"].copy()
        self.model = LGBMRegressor(**params)
        self.is_fitted = False
        self.feature_importance: dict[str, float] = {}

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
        """
        Train the model on historical data.

        Args:
            X: Feature DataFrame
            y: Target points

        Returns:
            Training metrics
        """
        # Select and validate features
        available_features = [f for f in FEATURE_COLUMNS if f in X.columns]
        if len(available_features) < len(FEATURE_COLUMNS) / 2:
            logger.warning(
                f"Only {len(available_features)}/{len(FEATURE_COLUMNS)} features available"
            )

        X_train = X[available_features].copy()

        # Fill NaN with 0
        X_train = X_train.fillna(0)

        # Train
        logger.info(f"Training on {len(X_train)} samples with {len(available_features)} features")
        self.model.fit(X_train, y)
        self.is_fitted = True

        # Store feature importance
        self.feature_importance = dict(
            zip(available_features, self.model.feature_importances_)
        )

        # Cross-validation using TimeSeriesSplit to avoid data leakage
        # Random CV mixes future data with past, which is wrong for time series
        n_samples = len(X_train)
        if n_samples >= 10:
            # Use TimeSeriesSplit: train on past, validate on future
            n_splits = min(5, n_samples // 2)
            tscv = TimeSeriesSplit(n_splits=n_splits)
            cv_scores = cross_val_score(
                self.model, X_train, y, cv=tscv, scoring="neg_mean_absolute_error"
            )
            cv_mae = -cv_scores.mean()
            cv_mae_std = cv_scores.std()
        elif n_samples >= 4:
            # Smaller dataset: use 2-fold time split
            tscv = TimeSeriesSplit(n_splits=2)
            cv_scores = cross_val_score(
                self.model, X_train, y, cv=tscv, scoring="neg_mean_absolute_error"
            )
            cv_mae = -cv_scores.mean()
            cv_mae_std = cv_scores.std()
        else:
            # Cannot do CV with < 4 samples
            logger.warning("Too few samples for cross-validation, skipping CV")
            cv_mae = 0.0
            cv_mae_std = 0.0

        return {
            "n_samples": n_samples,
            "n_features": len(available_features),
            "cv_mae": cv_mae,
            "cv_mae_std": cv_mae_std,
            "top_features": sorted(
                self.feature_importance.items(), key=lambda x: -x[1]
            )[:10],
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict points for players.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predicted points
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        available_features = [f for f in FEATURE_COLUMNS if f in X.columns]
        X_pred = X[available_features].fillna(0)

        predictions = self.model.predict(X_pred)

        # Ensure non-negative predictions
        predictions = np.maximum(predictions, 0)

        return predictions

    def save(self, path: str | Path) -> None:
        """Save model to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "is_fitted": self.is_fitted,
                    "feature_importance": self.feature_importance,
                },
                f,
            )

    def load(self, path: str | Path) -> None:
        """Load model from file."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.is_fitted = data["is_fitted"]
            self.feature_importance = data["feature_importance"]
