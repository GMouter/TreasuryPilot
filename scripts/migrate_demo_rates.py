"""Correct legacy demo FX rates to GBP-per-foreign-unit quotes.

This only updates the named demo companies and their currency rows.
Run from the repository root with the project virtual environment active:
    python scripts/migrate_demo_rates.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database.database import SessionLocal
from app.models.company import Company
from app.models.exposure import Exposure


DEMO_RATE_FIXES = {
    "Northstar Imports Ltd": {"USD": 0.79, "EUR": 0.85},
    "Alpine Components GmbH": {"GBP": 1.16, "USD": 0.93, "JPY": 0.0060},
    "Orbit Systems Inc": {"EUR": 1.08, "GBP": 1.27, "JPY": 0.0067},
    "Harbour & Field Co": {"USD": 0.79},
}


def migrate_demo_rates():
    db = SessionLocal()
    updated = 0
    try:
        for company_name, currency_rates in DEMO_RATE_FIXES.items():
            company = (
                db.query(Company)
                .filter(Company.name == company_name)
                .first()
            )
            if company is None:
                continue

            exposures = (
                db.query(Exposure)
                .filter(Exposure.company_id == company.id)
                .all()
            )
            for exposure in exposures:
                corrected_rate = currency_rates.get(exposure.currency)
                if corrected_rate is not None and exposure.current_fx_rate != corrected_rate:
                    exposure.current_fx_rate = corrected_rate
                    updated += 1

        db.commit()
        return updated
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Updated {migrate_demo_rates()} demo exposure rates.")
