import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class ConstructorStanding(IdMixin, IngestedMixin, Base):
    __tablename__ = "constructor_standings"
    __table_args__ = (UniqueConstraint("season_id", "round", "team_id"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"), index=True)
    round: Mapped[int]
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int]
    points: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    wins: Mapped[int]


class DriverTeamStint(IdMixin, IngestedMixin, Base):
    __tablename__ = "driver_team_stints"
    __table_args__ = (UniqueConstraint("season_id", "driver_id", "team_id", "from_round"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    from_round: Mapped[int]
    to_round: Mapped[int | None]
