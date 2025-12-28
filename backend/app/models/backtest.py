"""Backtest results model."""

from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class BacktestResult(Base):
    """Results of comparing a prediction to actual dream team."""

    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gameweek_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gameweeks.id"), nullable=False, index=True
    )
    prediction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("predictions.id"), nullable=False, unique=True
    )

    # Metrics
    player_overlap: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-11
    points_ratio: Mapped[float] = mapped_column(
        DECIMAL(5, 4), nullable=False
    )  # predicted/actual
    actual_total: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_total: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    gameweek: Mapped["Gameweek"] = relationship(
        "Gameweek", back_populates="backtest_results"
    )
    prediction: Mapped["Prediction"] = relationship(
        "Prediction", back_populates="backtest_result"
    )

    def __repr__(self) -> str:
        return f"<BacktestResult gw={self.gameweek_id} overlap={self.player_overlap}/11>"
