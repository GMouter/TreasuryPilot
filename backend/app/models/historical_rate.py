from datetime import date

from sqlalchemy import Date, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class HistoricalRate(Base):
    __tablename__ = "historical_fx_rates"
    __table_args__ = (
        UniqueConstraint(
            "currency",
            "base_currency",
            "rate_date",
            name="uq_historical_fx_rate_pair_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
