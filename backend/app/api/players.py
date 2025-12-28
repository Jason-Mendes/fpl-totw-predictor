"""Player API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Player, Team
from app.schemas import PlayerSchema

router = APIRouter()


@router.get("", response_model=list[PlayerSchema])
def list_players(
    position: str | None = Query(None, description="Filter by position (GKP, DEF, MID, FWD)"),
    team_id: int | None = Query(None, description="Filter by team FPL ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[PlayerSchema]:
    """
    List players with optional filters.

    - **position**: Filter by position (GKP, DEF, MID, FWD)
    - **team_id**: Filter by team FPL ID
    - **limit**: Max players to return (default 100, max 1000)
    - **offset**: Pagination offset
    """
    query = db.query(Player).options(joinedload(Player.team))

    if position:
        query = query.filter(Player.position == position.upper())
    if team_id:
        team = db.query(Team).filter(Team.fpl_id == team_id).first()
        if team:
            query = query.filter(Player.team_id == team.id)

    players = query.order_by(Player.web_name).offset(offset).limit(limit).all()

    return [
        PlayerSchema(
            id=p.id,
            fpl_id=p.fpl_id,
            web_name=p.web_name,
            first_name=p.first_name,
            second_name=p.second_name,
            position=p.position,
            team_id=p.team_id,
            team_name=p.team.name if p.team else None,
            team_short_name=p.team.short_name if p.team else None,
            now_cost=p.now_cost,
            status=p.status,
            chance_of_playing=p.chance_of_playing,
            is_penalty_taker=p.is_penalty_taker,
            is_corner_taker=p.is_corner_taker,
            is_freekick_taker=p.is_freekick_taker,
        )
        for p in players
    ]


@router.get("/{player_id}", response_model=PlayerSchema)
def get_player(player_id: int, db: Session = Depends(get_db)) -> PlayerSchema:
    """Get a specific player by FPL ID."""
    player = (
        db.query(Player)
        .options(joinedload(Player.team))
        .filter(Player.fpl_id == player_id)
        .first()
    )
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return PlayerSchema(
        id=player.id,
        fpl_id=player.fpl_id,
        web_name=player.web_name,
        first_name=player.first_name,
        second_name=player.second_name,
        position=player.position,
        team_id=player.team_id,
        team_name=player.team.name if player.team else None,
        team_short_name=player.team.short_name if player.team else None,
        now_cost=player.now_cost,
        status=player.status,
        chance_of_playing=player.chance_of_playing,
        is_penalty_taker=player.is_penalty_taker,
        is_corner_taker=player.is_corner_taker,
        is_freekick_taker=player.is_freekick_taker,
    )
