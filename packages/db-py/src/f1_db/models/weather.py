import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin


class WeatherSample(IdMixin, Base):
    __tablename__ = "weather_samples"
    __table_args__ = (UniqueConstraint("race_id", "observed_at", "source"),)
    race_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("races.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    air_temp_c: Mapped[float | None]
    track_temp_c: Mapped[float | None]
    humidity: Mapped[float | None]
    wind_kph: Mapped[float | None]
    rain_probability: Mapped[float | None]
    source: Mapped[str]
