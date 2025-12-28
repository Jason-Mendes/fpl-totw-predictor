"""Data sync API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SyncResultSchema
from app.services.data_ingestion import sync_fpl_data
from app.services.understat_sync import sync_understat_data

router = APIRouter()


@router.post("/fpl", response_model=SyncResultSchema)
def sync_fpl_endpoint(db: Session = Depends(get_db)) -> SyncResultSchema:
    """
    Sync all FPL data from the official API.

    This fetches:
    - Teams
    - Players
    - Gameweeks
    - Fixtures
    - Player stats for finished gameweeks
    - Dream teams for finished gameweeks
    """
    result = sync_fpl_data(db)
    return SyncResultSchema(**result)


@router.post("/understat")
def sync_understat_endpoint(
    season: str = "2024",
    db: Session = Depends(get_db),
) -> dict:
    """
    Sync xG/xA data from Understat.

    This fetches expected goals data for all EPL players and
    matches them to FPL players for enhanced predictions.

    Args:
        season: Season year (e.g., "2024" for 2024/25 season)
    """
    result = sync_understat_data(db, season)
    return result


@router.post("/all")
def sync_all_endpoint(
    season: str = "2024",
    db: Session = Depends(get_db),
) -> dict:
    """
    Sync all data sources (FPL + Understat).
    """
    fpl_result = sync_fpl_data(db)
    understat_result = sync_understat_data(db, season)

    return {
        "fpl": fpl_result,
        "understat": understat_result,
    }
