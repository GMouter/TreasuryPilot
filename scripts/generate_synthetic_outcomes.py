"""Generate labelled synthetic outcomes from stored public FX history.

This does not represent real company hedge activity. It is a repeatable
benchmark fixture for testing the outcome evaluation pipeline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database.database import Base, SessionLocal, engine
from app.models.company import Company
from app.models.exposure import Exposure
from app.models.historical_rate import HistoricalRate
from app.models.outcome import ExposureOutcome
from app.services.synthetic_outcomes import generate_synthetic_outcomes


def generate_for_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    created = 0
    skipped = 0
    try:
        exposures = db.query(Exposure).all()
        for exposure in exposures:
            company = db.query(Company).filter(Company.id == exposure.company_id).first()
            if company is None:
                continue
            if db.query(ExposureOutcome).filter(ExposureOutcome.exposure_id == exposure.id).first():
                skipped += 1
                continue
            observations = [
                {"date": rate.rate_date.isoformat(), "rate": rate.rate}
                for rate in (
                    db.query(HistoricalRate)
                    .filter(
                        HistoricalRate.currency == exposure.currency,
                        HistoricalRate.base_currency == company.base_currency,
                    )
                    .order_by(HistoricalRate.rate_date)
                    .all()
                )
            ]
            outcomes = generate_synthetic_outcomes(
                exposure_id=exposure.id,
                foreign_amount=exposure.foreign_amount,
                hedge_percentage=exposure.hedge_percentage,
                observations=observations,
            )
            db.add_all(ExposureOutcome(**outcome) for outcome in outcomes)
            created += len(outcomes)
        db.commit()
        return created, skipped
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    created, skipped = generate_for_database()
    print(f"Created {created} synthetic outcomes; skipped {skipped} exposures with existing outcomes.")
