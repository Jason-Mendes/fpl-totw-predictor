"""Player gameweek stats model."""

from sqlalchemy import DECIMAL, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlayerGWStats(Base):
    """Player statistics for a single gameweek."""

    __tablename__ = "player_gw_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    gameweek_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gameweeks.id"), nullable=False, index=True
    )
    fixture_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fixtures.id"), nullable=True
    )

    # Core stats
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    goals_scored: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    clean_sheets: Mapped[int] = mapped_column(Integer, default=0)
    goals_conceded: Mapped[int] = mapped_column(Integer, default=0)
    own_goals: Mapped[int] = mapped_column(Integer, default=0)
    penalties_saved: Mapped[int] = mapped_column(Integer, default=0)
    penalties_missed: Mapped[int] = mapped_column(Integer, default=0)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    bonus: Mapped[int] = mapped_column(Integer, default=0)
    bps: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0)

    # Underlying performance stats
    shots: Mapped[int] = mapped_column(Integer, default=0)
    key_passes: Mapped[int] = mapped_column(Integer, default=0)

    # xG/xA from Understat (nullable until synced)
    xg: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    xa: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    npxg: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="gw_stats")
    gameweek: Mapped["Gameweek"] = relationship("Gameweek", back_populates="player_stats")
    fixture: Mapped["Fixture"] = relationship("Fixture", back_populates="player_stats")

    __table_args__ = (
        UniqueConstraint("player_id", "gameweek_id", name="uq_player_gameweek"),
    )

    def __repr__(self) -> str:
        return f"<PlayerGWStats player={self.player_id} gw={self.gameweek_id} pts={self.total_points}>"
