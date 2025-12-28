"""Prediction models."""

from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Prediction(Base):
    """Predicted Team of the Week for a gameweek."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gameweek_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gameweeks.id"), nullable=False, index=True
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    total_predicted_points: Mapped[int] = mapped_column(Integer, nullable=True)
    formation: Mapped[str] = mapped_column(String(10), nullable=True)  # e.g., "4-5-1"

    # Relationships
    gameweek: Mapped["Gameweek"] = relationship("Gameweek", back_populates="predictions")
    players: Mapped[list["PredictionPlayer"]] = relationship(
        "PredictionPlayer", back_populates="prediction", cascade="all, delete-orphan"
    )
    backtest_result: Mapped["BacktestResult"] = relationship(
        "BacktestResult", back_populates="prediction", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Prediction gw={self.gameweek_id} v={self.model_version}>"


class PredictionPlayer(Base):
    """Individual player in a prediction."""

    __tablename__ = "prediction_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("predictions.id"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    position_slot: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-11
    predicted_points: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    predicted_minutes: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    start_probability: Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=True)
    confidence: Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=True)

    # Relationships
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="players")
    player: Mapped["Player"] = relationship("Player", back_populates="prediction_entries")

    def __repr__(self) -> str:
        return f"<PredictionPlayer pred={self.prediction_id} player={self.player_id} pts={self.predicted_points}>"
