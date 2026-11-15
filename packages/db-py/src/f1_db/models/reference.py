import uuid
from datetime import date

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class Season(IdMixin, Base):
    __tablename__ = "seasons"
    year: Mapped[int] = mapped_column(unique=True)


class Team(IdMixin, IngestedMixin, Base):
    __tablename__ = "teams"
    ref: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    nationality: Mapped[str | None]


class Driver(IdMixin, IngestedMixin, Base):
    __tablename__ = "drivers"
    ref: Mapped[str] = mapped_column(unique=True)
    code: Mapped[str | None]
    given_name: Mapped[str]
    family_name: Mapped[str]
    number: Mapped[int | None]
    nationality: Mapped[str | None]


class Race(IdMixin, IngestedMixin, Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season_id", "round"),)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id"))
    round: Mapped[int]
    name: Mapped[str]
    circuit_name: Mapped[str]
    race_date: Mapped[date]
