"""Fixture model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Fixture(Base):
    """Premier League fixture."""

    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fpl_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    gameweek_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gameweeks.id"), nullable=True
    )
    team_home_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    team_away_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )

    kickoff_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    difficulty_home: Mapped[int] = mapped_column(Integer, nullable=True)
    difficulty_away: Mapped[int] = mapped_column(Integer, nullable=True)
    team_h_score: Mapped[int] = mapped_column(Integer, nullable=True)
    team_a_score: Mapped[int] = mapped_column(Integer, nullable=True)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    gameweek: Mapped["Gameweek"] = relationship("Gameweek", back_populates="fixtures")
    team_home: Mapped["Team"] = relationship(
        "Team", foreign_keys=[team_home_id], back_populates="home_fixtures"
    )
    team_away: Mapped["Team"] = relationship(
        "Team", foreign_keys=[team_away_id], back_populates="away_fixtures"
    )
    player_stats: Mapped[list["PlayerGWStats"]] = relationship(
        "PlayerGWStats", back_populates="fixture"
    )

    def __repr__(self) -> str:
        return f"<Fixture {self.team_home_id} vs {self.team_away_id}>"
