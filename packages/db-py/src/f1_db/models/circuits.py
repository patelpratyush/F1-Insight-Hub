from sqlalchemy.orm import Mapped, mapped_column

from f1_db.base import Base, IdMixin, IngestedMixin


class Circuit(IdMixin, IngestedMixin, Base):
    __tablename__ = "circuits"
    ref: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    locality: Mapped[str]
    country: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]
