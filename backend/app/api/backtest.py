"""Backtest API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BacktestResult, Gameweek
from app.schemas import BacktestResultSchema, BacktestSummarySchema

router = APIRouter()


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
            min_overlap=0,
            max_overlap=0,
            weeks_above_9=0,
            weeks_above_8=0,
            results=[],
        )

    overlaps = [r.player_overlap for r in results]
    ratios = [float(r.points_ratio) for r in results]

    result_schemas = [
        BacktestResultSchema(
            gameweek_id=r.gameweek_id,
            gameweek_fpl_id=r.gameweek.fpl_id,
            player_overlap=r.player_overlap,
            points_ratio=float(r.points_ratio),
            actual_total=r.actual_total,
            predicted_total=r.predicted_total,
            created_at=r.created_at,
        )
        for r in results
    ]

    return BacktestSummarySchema(
        total_gameweeks=len(results),
        avg_overlap=sum(overlaps) / len(overlaps),
        avg_points_ratio=sum(ratios) / len(ratios),
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

    return BacktestResultSchema(
        gameweek_id=result.gameweek_id,
        gameweek_fpl_id=gw.fpl_id,
        player_overlap=result.player_overlap,
        points_ratio=float(result.points_ratio),
        actual_total=result.actual_total,
        predicted_total=result.predicted_total,
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
