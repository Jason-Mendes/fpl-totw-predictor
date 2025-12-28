"""Player model."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    """FPL player."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fpl_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=True)
    understat_id: Mapped[int] = mapped_column(Integer, nullable=True)

    # Names
    web_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    second_name: Mapped[str] = mapped_column(String(100), nullable=True)

    # Position: GKP, DEF, MID, FWD
    position: Mapped[str] = mapped_column(String(10), nullable=False)

    # Current state
    now_cost: Mapped[int] = mapped_column(Integer, nullable=True)  # Price x10
    status: Mapped[str] = mapped_column(String(20), nullable=True)  # a, d, i, n, s, u
    chance_of_playing: Mapped[int] = mapped_column(Integer, nullable=True)
    news: Mapped[str] = mapped_column(Text, nullable=True)

    # Set piece duties
    is_penalty_taker: Mapped[bool] = mapped_column(Boolean, default=False)
    is_corner_taker: Mapped[bool] = mapped_column(Boolean, default=False)
    is_freekick_taker: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="players")
    gw_stats: Mapped[list["PlayerGWStats"]] = relationship(
        "PlayerGWStats", back_populates="player"
    )
    dream_team_entries: Mapped[list["DreamTeam"]] = relationship(
        "DreamTeam", back_populates="player"
    )
    prediction_entries: Mapped[list["PredictionPlayer"]] = relationship(
        "PredictionPlayer", back_populates="player"
    )

    def __repr__(self) -> str:
        return f"<Player {self.web_name} ({self.position})>"
