"""Team model."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    """Premier League team."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fpl_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(10), nullable=True)
    strength_attack_home: Mapped[int] = mapped_column(Integer, nullable=True)
    strength_attack_away: Mapped[int] = mapped_column(Integer, nullable=True)
    strength_defence_home: Mapped[int] = mapped_column(Integer, nullable=True)
    strength_defence_away: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationships
    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")
    home_fixtures: Mapped[list["Fixture"]] = relationship(
        "Fixture", foreign_keys="Fixture.team_home_id", back_populates="team_home"
    )
    away_fixtures: Mapped[list["Fixture"]] = relationship(
        "Fixture", foreign_keys="Fixture.team_away_id", back_populates="team_away"
    )

    def __repr__(self) -> str:
        return f"<Team {self.short_name}>"
