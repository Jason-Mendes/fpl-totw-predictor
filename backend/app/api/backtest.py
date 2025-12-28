"""Backtest API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BacktestResult, Gameweek, PlayerGWStats, PredictionPlayer
from app.schemas import BacktestResultSchema, BacktestSummarySchema

router = APIRouter()


def _compute_predicted_team_actual(
    db: Session, prediction_id: int, gameweek_id: int
) -> int | None:
    """Compute the actual points scored by the predicted team."""
    pred_players = (
        db.query(PredictionPlayer)
        .filter(PredictionPlayer.prediction_id == prediction_id)
        .all()
    )
    if not pred_players:
        return None

    total = 0
    for pp in pred_players:
        stats = (
            db.query(PlayerGWStats)
            .filter(
                PlayerGWStats.player_id == pp.player_id,
                PlayerGWStats.gameweek_id == gameweek_id,
            )
            .first()
        )
        if stats:
            total += stats.total_points
    return total


@router.get("/summary", response_model=BacktestSummarySchema)
def get_backtest_summary(db: Session = Depends(get_db)) -> BacktestSummarySchema:
    """Get summary of all backtest results."""
    results = (
        db.query(BacktestResult)
        .join(Gameweek)
        .order_by(Gameweek.fpl_id)
        .all()
    )

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
    ratios = [float(r.points_ratio) for r in results]
    dream_team_points = [r.actual_total for r in results]

    # Compute predicted_team_actual for each result
    result_schemas = []
    predicted_team_actuals = []
    for r in results:
        pta = _compute_predicted_team_actual(db, r.prediction_id, r.gameweek_id)
        if pta is not None:
            predicted_team_actuals.append(pta)
        result_schemas.append(
            BacktestResultSchema(
                gameweek_id=r.gameweek_id,
                gameweek_fpl_id=r.gameweek.fpl_id,
                player_overlap=r.player_overlap,
                points_ratio=float(r.points_ratio),
                actual_total=r.actual_total,
                predicted_total=r.predicted_total,
                predicted_team_actual=pta,
                created_at=r.created_at,
            )
        )

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
        results=result_schemas,
    )


@router.get("/{gw_id}", response_model=BacktestResultSchema | None)
def get_backtest_result(
    gw_id: int, db: Session = Depends(get_db)
) -> BacktestResultSchema | None:
    """Get backtest result for a specific gameweek."""
    gw = db.query(Gameweek).filter(Gameweek.fpl_id == gw_id).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gameweek not found")

    result = db.query(BacktestResult).filter(BacktestResult.gameweek_id == gw.id).first()
    if not result:
        return None

    # Compute actual points scored by our predicted team
    predicted_team_actual = _compute_predicted_team_actual(
        db, result.prediction_id, result.gameweek_id
    )

    return BacktestResultSchema(
        gameweek_id=result.gameweek_id,
        gameweek_fpl_id=gw.fpl_id,
        player_overlap=result.player_overlap,
        points_ratio=float(result.points_ratio),
        actual_total=result.actual_total,
        predicted_total=result.predicted_total,
        predicted_team_actual=predicted_team_actual,
        created_at=result.created_at,
    )


@router.post("/run")
def run_backtest(
    start_gw: int = Query(6, description="Start gameweek (min 6 for enough history)"),
    end_gw: int | None = Query(None, description="End gameweek (defaults to last finished)"),
    db: Session = Depends(get_db),
) -> BacktestSummarySchema:
    """
    Run backtest across gameweeks.

    This trains the model on data before each GW and predicts that GW,
    then compares to the actual dream team.
    """
    from app.services.backtest import run_backtest as run_bt

    summary = run_bt(db, start_gw, end_gw)
    return summary
