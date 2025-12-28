"""Gameweek model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Gameweek(Base):
    """FPL gameweek."""

    __tablename__ = "gameweeks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fpl_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_next: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    fixtures: Mapped[list["Fixture"]] = relationship("Fixture", back_populates="gameweek")
    player_stats: Mapped[list["PlayerGWStats"]] = relationship(
        "PlayerGWStats", back_populates="gameweek"
    )
    dream_team_entries: Mapped[list["DreamTeam"]] = relationship(
        "DreamTeam", back_populates="gameweek"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="gameweek"
    )
    backtest_results: Mapped[list["BacktestResult"]] = relationship(
        "BacktestResult", back_populates="gameweek"
    )

    def __repr__(self) -> str:
        return f"<Gameweek {self.fpl_id}>"
