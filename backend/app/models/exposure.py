from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Exposure(Base):
    __tablename__ = "exposures"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    foreign_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    current_fx_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    hedge_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=75.0,
    )