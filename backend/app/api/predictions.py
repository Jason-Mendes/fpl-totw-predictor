"""Prediction API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import DreamTeam, Gameweek, Player, Prediction
from app.schemas import (
    DreamTeamPlayerSchema,
    DreamTeamSchema,
    PredictionPlayerSchema,
    PredictionSchema,
)

router = APIRouter()


@router.get("/{gw_id}", response_model=PredictionSchema | None)
def get_prediction(gw_id: int, db: Session = Depends(get_db)) -> PredictionSchema | None:
    """
    Get the predicted Team of the Week for a gameweek.

    Args:
        gw_id: Gameweek FPL ID (1-38)
    """
    gw = db.query(Gameweek).filter(Gameweek.fpl_id == gw_id).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gameweek not found")

    prediction = (
        db.query(Prediction)
        .options(joinedload(Prediction.players).joinedload("player").joinedload("team"))
        .filter(Prediction.gameweek_id == gw.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    if not prediction:
        return None

    players = []
    for pp in sorted(prediction.players, key=lambda x: x.position_slot):
        player = pp.player
        players.append(
            PredictionPlayerSchema(
                player_id=player.id,
                player_fpl_id=player.fpl_id,
                web_name=player.web_name,
                position=player.position,
                team_short_name=player.team.short_name if player.team else None,
                position_slot=pp.position_slot,
                predicted_points=float(pp.predicted_points),
                predicted_minutes=float(pp.predicted_minutes) if pp.predicted_minutes else None,
                start_probability=float(pp.start_probability) if pp.start_probability else None,
                confidence=float(pp.confidence) if pp.confidence else None,
            )
        )

    return PredictionSchema(
        id=prediction.id,
        gameweek_id=gw.id,
        gameweek_fpl_id=gw.fpl_id,
        model_version=prediction.model_version,
        created_at=prediction.created_at,
        total_predicted_points=prediction.total_predicted_points,
        formation=prediction.formation,
        players=players,
    )


@router.get("/dream-team/{gw_id}", response_model=DreamTeamSchema | None)
def get_dream_team(gw_id: int, db: Session = Depends(get_db)) -> DreamTeamSchema | None:
    """
    Get the actual Dream Team (ground truth) for a gameweek.

    Args:
        gw_id: Gameweek FPL ID (1-38)
    """
    gw = db.query(Gameweek).filter(Gameweek.fpl_id == gw_id).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gameweek not found")

    dream_team_entries = (
        db.query(DreamTeam)
        .options(joinedload(DreamTeam.player).joinedload(Player.team))
        .filter(DreamTeam.gameweek_id == gw.id)
        .order_by(DreamTeam.position_slot)
        .all()
    )

    if not dream_team_entries:
        return None

    players = []
    total_points = 0
    for dt in dream_team_entries:
        player = dt.player
        players.append(
            DreamTeamPlayerSchema(
                player_id=player.id,
                player_fpl_id=player.fpl_id,
                web_name=player.web_name,
                position=player.position,
                team_short_name=player.team.short_name if player.team else None,
                position_slot=dt.position_slot,
                points=dt.points,
            )
        )
        total_points += dt.points

    return DreamTeamSchema(
        gameweek_id=gw.id,
        gameweek_fpl_id=gw.fpl_id,
        total_points=total_points,
        players=players,
    )


@router.post("/generate/{gw_id}", response_model=PredictionSchema)
def generate_prediction(gw_id: int, db: Session = Depends(get_db)) -> PredictionSchema:
    """
    Generate a new prediction for a gameweek.

    Args:
        gw_id: Gameweek FPL ID (1-38)
    """
    # Import here to avoid circular imports
    from app.services.predictor import generate_prediction as gen_pred

    gw = db.query(Gameweek).filter(Gameweek.fpl_id == gw_id).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gameweek not found")

    prediction = gen_pred(db, gw_id)
    if not prediction:
        raise HTTPException(
            status_code=400,
            detail="Could not generate prediction. Not enough historical data.",
        )

    # Reload with relationships
    prediction = (
        db.query(Prediction)
        .options(joinedload(Prediction.players).joinedload("player").joinedload("team"))
        .filter(Prediction.id == prediction.id)
        .first()
    )

    players = []
    for pp in sorted(prediction.players, key=lambda x: x.position_slot):
        player = pp.player
        players.append(
            PredictionPlayerSchema(
                player_id=player.id,
                player_fpl_id=player.fpl_id,
                web_name=player.web_name,
                position=player.position,
                team_short_name=player.team.short_name if player.team else None,
                position_slot=pp.position_slot,
                predicted_points=float(pp.predicted_points),
                predicted_minutes=float(pp.predicted_minutes) if pp.predicted_minutes else None,
                start_probability=float(pp.start_probability) if pp.start_probability else None,
                confidence=float(pp.confidence) if pp.confidence else None,
            )
        )

    return PredictionSchema(
        id=prediction.id,
        gameweek_id=gw.id,
        gameweek_fpl_id=gw.fpl_id,
        model_version=prediction.model_version,
        created_at=prediction.created_at,
        total_predicted_points=prediction.total_predicted_points,
        formation=prediction.formation,
        players=players,
    )
