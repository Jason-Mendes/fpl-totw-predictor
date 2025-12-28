"""Gameweek API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Gameweek
from app.schemas import GameweekSchema

router = APIRouter()


@router.get("", response_model=list[GameweekSchema])
def list_gameweeks(db: Session = Depends(get_db)) -> list[GameweekSchema]:
    """Get all gameweeks."""
    gameweeks = db.query(Gameweek).order_by(Gameweek.fpl_id).all()
    return [GameweekSchema.model_validate(gw) for gw in gameweeks]


@router.get("/current", response_model=GameweekSchema | None)
def get_current_gameweek(db: Session = Depends(get_db)) -> GameweekSchema | None:
    """Get the current gameweek."""
    gw = db.query(Gameweek).filter(Gameweek.is_current == True).first()  # noqa: E712
    if not gw:
        return None
    return GameweekSchema.model_validate(gw)


@router.get("/next", response_model=GameweekSchema | None)
def get_next_gameweek(db: Session = Depends(get_db)) -> GameweekSchema | None:
    """Get the next gameweek."""
    gw = db.query(Gameweek).filter(Gameweek.is_next == True).first()  # noqa: E712
    if not gw:
        return None
    return GameweekSchema.model_validate(gw)


@router.get("/{gw_id}", response_model=GameweekSchema)
def get_gameweek(gw_id: int, db: Session = Depends(get_db)) -> GameweekSchema:
    """Get a specific gameweek by FPL ID."""
    gw = db.query(Gameweek).filter(Gameweek.fpl_id == gw_id).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gameweek not found")
    return GameweekSchema.model_validate(gw)
