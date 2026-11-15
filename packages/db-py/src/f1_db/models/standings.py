import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class DriverStanding(IdMixin, IngestedMixin, Base):
    __tablename__ = "driver_standings"
    __table_args__ = (UniqueConstraint("season_id", "round", "driver_id"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"), index=True)
    round: Mapped[int]
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int]
    points: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    wins: Mapped[int]
