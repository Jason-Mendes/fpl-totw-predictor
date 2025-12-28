"""Backtesting service for evaluating prediction accuracy."""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.constants import MIN_GAMEWEEKS_FOR_PREDICTION
from app.models import (
    BacktestResult,
    DreamTeam,
    Gameweek,
    Prediction,
    PredictionPlayer,
)
from app.schemas import BacktestResultSchema, BacktestSummarySchema
from app.services.predictor import generate_prediction

logger = logging.getLogger(__name__)


def run_backtest(
    db: Session,
    start_gw: int,
    end_gw: int | None = None,
) -> BacktestSummarySchema:
    """
    Run backtesting across multiple gameweeks.

    For each gameweek, trains a model using only data available before that GW,
    generates a prediction, and compares to the actual Dream Team.

    Args:
        db: Database session
        start_gw: First gameweek to backtest (should be >= MIN_GAMEWEEKS + 1)
        end_gw: Last gameweek to backtest (defaults to last finished GW)

    Returns:
        BacktestSummarySchema with results
    """
    # Determine end gameweek if not specified
    if end_gw is None:
        last_finished = (
            db.query(Gameweek)
            .filter(Gameweek.finished == True)  # noqa: E712
            .order_by(Gameweek.fpl_id.desc())
            .first()
        )
        if last_finished:
            end_gw = last_finished.fpl_id
        else:
            return BacktestSummarySchema(
                total_gameweeks=0,
                avg_overlap=0.0,
                avg_points_ratio=0.0,
                min_overlap=0,
                max_overlap=0,
                weeks_above_9=0,
                weeks_above_8=0,
                results=[],
            )

    # Ensure start_gw is valid
    min_valid_start = MIN_GAMEWEEKS_FOR_PREDICTION + 1
    if start_gw < min_valid_start:
        logger.warning(
            f"start_gw {start_gw} too early, adjusting to {min_valid_start}"
        )
        start_gw = min_valid_start

    results: list[BacktestResultSchema] = []

    for gw in range(start_gw, end_gw + 1):
        logger.info(f"Backtesting GW {gw}...")

        # Check if we have dream team data for this GW
        gw_db = db.query(Gameweek).filter(Gameweek.fpl_id == gw).first()
        if not gw_db or not gw_db.finished:
            logger.info(f"Skipping GW {gw} - not finished")
            continue

        dream_team_entries = (
            db.query(DreamTeam).filter(DreamTeam.gameweek_id == gw_db.id).all()
        )
        if len(dream_team_entries) != 11:
            logger.info(f"Skipping GW {gw} - incomplete dream team data")
            continue

        # Check if we already have a prediction for this GW
        existing_prediction = (
            db.query(Prediction)
            .filter(Prediction.gameweek_id == gw_db.id)
            .first()
        )

        if existing_prediction:
            prediction = existing_prediction
        else:
            # Generate prediction
            prediction = generate_prediction(db, gw)
            if not prediction:
                logger.warning(f"Could not generate prediction for GW {gw}")
                continue

        # Get predicted player IDs
        pred_players = (
            db.query(PredictionPlayer)
            .filter(PredictionPlayer.prediction_id == prediction.id)
            .all()
        )
        predicted_player_ids = {pp.player_id for pp in pred_players}

        # Get actual dream team player IDs
        actual_player_ids = {dt.player_id for dt in dream_team_entries}

        # Calculate overlap
        overlap = len(predicted_player_ids & actual_player_ids)

        # Calculate points
        predicted_total = prediction.total_predicted_points or 0
        actual_total = sum(dt.points for dt in dream_team_entries)

        # Calculate points ratio (avoid division by zero)
        points_ratio = (
            predicted_total / actual_total if actual_total > 0 else 0.0
        )

        # Check if backtest result already exists
        existing_result = (
            db.query(BacktestResult)
            .filter(BacktestResult.prediction_id == prediction.id)
            .first()
        )

        if existing_result:
            # Update existing
            existing_result.player_overlap = overlap
            existing_result.points_ratio = Decimal(str(points_ratio))
            existing_result.actual_total = actual_total
            existing_result.predicted_total = predicted_total
        else:
            # Create new backtest result
            bt_result = BacktestResult(
                gameweek_id=gw_db.id,
                prediction_id=prediction.id,
                player_overlap=overlap,
                points_ratio=Decimal(str(points_ratio)),
                actual_total=actual_total,
                predicted_total=predicted_total,
            )
            db.add(bt_result)

        db.commit()

        results.append(
            BacktestResultSchema(
                gameweek_id=gw_db.id,
                gameweek_fpl_id=gw,
                player_overlap=overlap,
                points_ratio=points_ratio,
                actual_total=actual_total,
                predicted_total=predicted_total,
                created_at=prediction.created_at,
            )
        )

        logger.info(
            f"GW {gw}: Overlap {overlap}/11, "
            f"Points ratio {points_ratio:.2%}, "
            f"Predicted {predicted_total}, Actual {actual_total}"
        )

    # Calculate summary stats
    if not results:
        return BacktestSummarySchema(
            total_gameweeks=0,
            avg_overlap=0.0,
            avg_points_ratio=0.0,
            min_overlap=0,
            max_overlap=0,
            weeks_above_9=0,
            weeks_above_8=0,
            results=[],
        )

    overlaps = [r.player_overlap for r in results]
    ratios = [r.points_ratio for r in results]

    return BacktestSummarySchema(
        total_gameweeks=len(results),
        avg_overlap=sum(overlaps) / len(overlaps),
        avg_points_ratio=sum(ratios) / len(ratios),
        min_overlap=min(overlaps),
        max_overlap=max(overlaps),
        weeks_above_9=sum(1 for o in overlaps if o >= 9),
        weeks_above_8=sum(1 for o in overlaps if o >= 8),
        results=results,
    )


def evaluate_single_prediction(
    db: Session,
    prediction_id: int,
) -> BacktestResultSchema | None:
    """
    Evaluate a single prediction against the actual dream team.

    Args:
        db: Database session
        prediction_id: ID of the prediction to evaluate

    Returns:
        BacktestResultSchema or None if not possible
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        return None

    gw = db.query(Gameweek).filter(Gameweek.id == prediction.gameweek_id).first()
    if not gw or not gw.finished:
        return None

    dream_team = db.query(DreamTeam).filter(DreamTeam.gameweek_id == gw.id).all()
    if len(dream_team) != 11:
        return None

    pred_players = (
        db.query(PredictionPlayer)
        .filter(PredictionPlayer.prediction_id == prediction.id)
        .all()
    )

    predicted_ids = {pp.player_id for pp in pred_players}
    actual_ids = {dt.player_id for dt in dream_team}

    overlap = len(predicted_ids & actual_ids)
    actual_total = sum(dt.points for dt in dream_team)
    predicted_total = prediction.total_predicted_points or 0
    points_ratio = predicted_total / actual_total if actual_total > 0 else 0.0

    return BacktestResultSchema(
        gameweek_id=gw.id,
        gameweek_fpl_id=gw.fpl_id,
        player_overlap=overlap,
        points_ratio=points_ratio,
        actual_total=actual_total,
        predicted_total=predicted_total,
        created_at=prediction.created_at,
    )
