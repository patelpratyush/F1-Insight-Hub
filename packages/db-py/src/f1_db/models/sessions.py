import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class RaceSession(IdMixin, IngestedMixin, Base):
    __tablename__ = "race_sessions"
    __table_args__ = (UniqueConstraint("race_id", "type"),)
    race_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("races.id"), index=True)
    type: Mapped[str]  # FP1 FP2 FP3 SQ SPRINT Q R
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(default="scheduled")  # scheduled live finished cancelled
    openf1_session_key: Mapped[int | None]


class LapRecord(IdMixin, IngestedMixin, Base):
    __tablename__ = "laps"
    __table_args__ = (UniqueConstraint("race_session_id", "driver_id", "lap_number"),)
    race_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("race_sessions.id"), index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    lap_number: Mapped[int]
    lap_time_ms: Mapped[int | None]
    s1_ms: Mapped[int | None]
    s2_ms: Mapped[int | None]
    s3_ms: Mapped[int | None]
    is_pit_out: Mapped[bool] = mapped_column(default=False)
    compound: Mapped[str | None]


class PitStop(IdMixin, IngestedMixin, Base):
    __tablename__ = "pit_stops"
    __table_args__ = (UniqueConstraint("race_session_id", "driver_id", "lap_number"),)
    race_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("race_sessions.id"), index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    lap_number: Mapped[int]
    duration_ms: Mapped[int | None]


class Stint(IdMixin, IngestedMixin, Base):
    __tablename__ = "stints"
    __table_args__ = (UniqueConstraint("race_session_id", "driver_id", "stint_number"),)
    race_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("race_sessions.id"), index=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    stint_number: Mapped[int]
    compound: Mapped[str]
    lap_start: Mapped[int]
    lap_end: Mapped[int | None]
