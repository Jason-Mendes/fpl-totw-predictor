"""Data sync API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SyncResultSchema
from app.services.data_ingestion import sync_fpl_data

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
