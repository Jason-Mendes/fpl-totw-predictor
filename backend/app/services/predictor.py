"""Prediction service for generating Dream Team predictions."""

import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import MIN_GAMEWEEKS_FOR_PREDICTION
from app.ml.formation_solver import PlayerPrediction, solve_formation
from app.ml.points_model import PointsPredictor
from app.models import Gameweek, Player, Prediction, PredictionPlayer
from app.services.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_prediction(db: Session, target_gw: int) -> Prediction | None:
    """
    Generate a Dream Team prediction for a gameweek.

    Args:
        db: Database session
        target_gw: FPL gameweek ID to predict for

    Returns:
        Prediction model instance, or None if not enough data
    """
    # Check if we have enough historical data
    finished_gws = (
        db.query(Gameweek)
        .filter(Gameweek.fpl_id < target_gw, Gameweek.finished == True)  # noqa: E712
        .count()
    )

    if finished_gws < MIN_GAMEWEEKS_FOR_PREDICTION:
        logger.warning(
            f"Not enough historical data. Have {finished_gws} GWs, "
            f"need {MIN_GAMEWEEKS_FOR_PREDICTION}"
        )
        return None

    # Get target gameweek
    target_gw_db = db.query(Gameweek).filter(Gameweek.fpl_id == target_gw).first()
    if not target_gw_db:
        logger.error(f"Gameweek {target_gw} not found")
        return None

    # Generate features
    feature_engineer = FeatureEngineer(db)

    # Get training data (all historical GWs before target)
    # Start from GW 1 - feature engineering handles partial data for early GWs
    # End at target_gw - 1 to avoid data leakage
    start_gw = 1
    end_gw = target_gw - 1

    if end_gw < 1:
        logger.error(f"Cannot predict GW {target_gw}: no historical data available")
        return None

    X_train, y_train = feature_engineer.get_training_data(start_gw, end_gw)
    if X_train.empty:
        logger.error("No training data available")
        return None

    # Train model
    model = PointsPredictor()
    metrics = model.train(X_train, y_train)
    logger.info(f"Model trained: CV MAE = {metrics['cv_mae']:.2f}")

    # Get features for prediction
    X_pred = feature_engineer.get_player_features_for_gameweek(target_gw)
    if X_pred.empty:
        logger.error("No prediction features available")
        return None

    # Make predictions
    predicted_points = model.predict(X_pred)
    X_pred["predicted_points"] = predicted_points

    # Map player IDs to Player objects
    player_ids = X_pred["player_id"].tolist()
    players = db.query(Player).filter(Player.id.in_(player_ids)).all()
    player_map = {p.id: p for p in players}

    # Build prediction objects
    predictions: list[PlayerPrediction] = []
    for _, row in X_pred.iterrows():
        player = player_map.get(int(row["player_id"]))
        if player:
            predictions.append(
                PlayerPrediction(
                    player_id=player.id,
                    player_fpl_id=player.fpl_id,
                    position=player.position,
                    predicted_points=row["predicted_points"],
                    web_name=player.web_name,
                )
            )

    # Solve for optimal XI
    selected_xi, formation = solve_formation(predictions)

    if not selected_xi:
        logger.error("Formation solver returned empty XI")
        return None

    # Calculate total predicted points (round the sum, not individual values)
    total_points = round(sum(p.predicted_points for p in selected_xi))

    # Create prediction record
    prediction = Prediction(
        gameweek_id=target_gw_db.id,
        model_version=settings.model_version,
        total_predicted_points=total_points,
        formation=formation,
    )
    db.add(prediction)
    db.flush()

    # Add prediction players
    for slot, pp in enumerate(selected_xi, start=1):
        pred_player = PredictionPlayer(
            prediction_id=prediction.id,
            player_id=pp.player_id,
            position_slot=slot,
            predicted_points=pp.predicted_points,
            predicted_minutes=90.0,  # Simplified - assume full games
            start_probability=0.95,  # Simplified
            confidence=0.7,  # Simplified
        )
        db.add(pred_player)

    db.commit()

    logger.info(
        f"Generated prediction for GW {target_gw}: "
        f"{formation} formation, {total_points} predicted points"
    )

    return prediction
