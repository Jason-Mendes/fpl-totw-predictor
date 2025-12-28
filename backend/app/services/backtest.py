"""Backtesting service for evaluating prediction accuracy."""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import MIN_GAMEWEEKS_FOR_PREDICTION
from app.models import (
    BacktestResult,
    DreamTeam,
    Gameweek,
    PlayerGWStats,
    Prediction,
    PredictionPlayer,
)
from app.schemas import BacktestResultSchema, BacktestSummarySchema
from app.services.predictor import ModelType, generate_prediction

logger = logging.getLogger(__name__)
settings = get_settings()


def run_backtest(
    db: Session,
    start_gw: int,
    end_gw: int | None = None,
    model_type: ModelType = "ensemble",
    force_regenerate: bool = False,
) -> BacktestSummarySchema:
    """
    Run backtesting across multiple gameweeks.

    For each gameweek, trains a model using only data available before that GW,
    generates a prediction, and compares to the actual Dream Team.

    Args:
        db: Database session
        start_gw: First gameweek to backtest (should be >= MIN_GAMEWEEKS + 1)
        end_gw: Last gameweek to backtest (defaults to last finished GW)
        model_type: Which model to use ("lgbm", "simple", or "ensemble")
        force_regenerate: If True, regenerate predictions even if they exist

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

        # Check if we already have a prediction for this GW with matching model_version
        # Model version format: "{settings.model_version}-{model_type}"
        expected_version = f"{settings.model_version}-{model_type}"
        existing_prediction = (
            db.query(Prediction)
            .filter(
                Prediction.gameweek_id == gw_db.id,
                Prediction.model_version == expected_version,
            )
            .first()
        )

        if existing_prediction and not force_regenerate:
            prediction = existing_prediction
            logger.info(
                f"Reusing existing prediction for GW {gw} "
                f"(version: {existing_prediction.model_version})"
            )
        else:
            # Delete existing prediction if force_regenerate
            if existing_prediction and force_regenerate:
                # Also delete associated backtest result
                db.query(BacktestResult).filter(
                    BacktestResult.prediction_id == existing_prediction.id
                ).delete()
                # Delete prediction players
                db.query(PredictionPlayer).filter(
                    PredictionPlayer.prediction_id == existing_prediction.id
                ).delete()
                # Delete prediction
                db.delete(existing_prediction)
                db.commit()

            # Generate prediction with specified model type
            prediction = generate_prediction(db, gw, model_type=model_type)
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

        # Calculate actual points scored by our predicted team
        predicted_team_actual = 0
        for pp in pred_players:
            # Get the actual stats for this player in this gameweek
            actual_stats = (
                db.query(PlayerGWStats)
                .filter(
                    PlayerGWStats.player_id == pp.player_id,
                    PlayerGWStats.gameweek_id == gw_db.id,
                )
                .first()
            )
            if actual_stats:
                predicted_team_actual += actual_stats.total_points

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
                predicted_team_actual=predicted_team_actual,
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
            avg_predicted_team_actual=None,
            avg_dream_team_points=None,
            min_overlap=0,
            max_overlap=0,
            weeks_above_9=0,
            weeks_above_8=0,
            results=[],
        )

    overlaps = [r.player_overlap for r in results]
    ratios = [r.points_ratio for r in results]
    predicted_team_actuals = [
        r.predicted_team_actual for r in results if r.predicted_team_actual is not None
    ]
    dream_team_points = [r.actual_total for r in results]

    return BacktestSummarySchema(
        total_gameweeks=len(results),
        avg_overlap=sum(overlaps) / len(overlaps),
        avg_points_ratio=sum(ratios) / len(ratios),
        avg_predicted_team_actual=(
            sum(predicted_team_actuals) / len(predicted_team_actuals)
            if predicted_team_actuals
            else None
        ),
        avg_dream_team_points=(
            sum(dream_team_points) / len(dream_team_points)
            if dream_team_points
            else None
        ),
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

    # Calculate actual points scored by our predicted team
    predicted_team_actual = 0
    for pp in pred_players:
        actual_stats = (
            db.query(PlayerGWStats)
            .filter(
                PlayerGWStats.player_id == pp.player_id,
                PlayerGWStats.gameweek_id == gw.id,
            )
            .first()
        )
        if actual_stats:
            predicted_team_actual += actual_stats.total_points

    return BacktestResultSchema(
        gameweek_id=gw.id,
        gameweek_fpl_id=gw.fpl_id,
        player_overlap=overlap,
        points_ratio=points_ratio,
        actual_total=actual_total,
        predicted_total=predicted_total,
        predicted_team_actual=predicted_team_actual,
        created_at=prediction.created_at,
    )
