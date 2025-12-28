"""Dream Team model - ground truth for predictions."""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DreamTeam(Base):
    """Actual FPL Dream Team (Team of the Week) for a gameweek."""

    __tablename__ = "dream_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gameweek_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gameweeks.id"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    position_slot: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-11
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    gameweek: Mapped["Gameweek"] = relationship(
        "Gameweek", back_populates="dream_team_entries"
    )
    player: Mapped["Player"] = relationship("Player", back_populates="dream_team_entries")

    __table_args__ = (
        UniqueConstraint("gameweek_id", "player_id", name="uq_dream_team_gw_player"),
    )

    def __repr__(self) -> str:
        return f"<DreamTeam gw={self.gameweek_id} player={self.player_id} pts={self.points}>"
