import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class SessionResult(IdMixin, IngestedMixin, Base):
    __tablename__ = "session_results"
    __table_args__ = (UniqueConstraint("race_id", "session_type", "driver_id"),)
    race_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("races.id"), index=True)
    session_type: Mapped[str]
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int | None]
    grid: Mapped[int | None]
    status: Mapped[str | None]
    points: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    time_ms: Mapped[int | None]
