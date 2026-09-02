from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class ExposureOutcome(Base):
    __tablename__ = "exposure_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exposure_id: Mapped[int] = mapped_column(ForeignKey("exposures.id"), nullable=False, index=True)
    decision_date: Mapped[date] = mapped_column(Date, nullable=False)
    decision_fx_rate: Mapped[float] = mapped_column(Float, nullable=False)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False)
    settlement_fx_rate: Mapped[float] = mapped_column(Float, nullable=False)
    hedge_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    hedge_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
