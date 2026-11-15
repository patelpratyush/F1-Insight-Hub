import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, utcnow


class IngestionRun(IdMixin, Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("ix_ingestion_runs_job_started", "job", "started_at"),)
    job: Mapped[str]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str]  # running | success | failed
    rows: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None]


_ = uuid  # keep import used for type checkers on some versions
