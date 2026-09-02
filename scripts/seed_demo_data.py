"""Create representative TreasuryPilot demo data.

Run from the repository root with the project virtual environment active:
    python scripts/seed_demo_data.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database.database import SessionLocal
from app.models.company import Company
from app.models.exposure import Exposure


DEMO_COMPANIES = [
    {
        "name": "Northstar Imports Ltd",
        "country": "United Kingdom",
        "base_currency": "GBP",
        "exposures": [
            ("USD", 1_250_000, 0.79, 18, 25),
            ("EUR", 450_000, 0.85, 62, 50),
        ],
    },
    {
        "name": "Alpine Components GmbH",
        "country": "Germany",
        "base_currency": "EUR",
        "exposures": [
            ("GBP", 600_000, 1.16, 45, 75),
            ("USD", 900_000, 0.93, 140, 50),
            ("JPY", 80_000_000, 0.0060, 210, 35),
        ],
    },
    {
        "name": "Orbit Systems Inc",
        "country": "United States",
        "base_currency": "USD",
        "exposures": [
            ("EUR", 800_000, 1.08, 30, 90),
            ("GBP", 300_000, 1.27, 95, 80),
            ("JPY", 45_000_000, 0.0067, 180, 60),
        ],
    },
    {
        "name": "Harbour & Field Co",
        "country": "United Kingdom",
        "base_currency": "GBP",
        "exposures": [
            ("USD", 75_000, 0.79, 120, 25),
        ],
    },
]


def seed_demo_data():
    db = SessionLocal()
    created_companies = 0
    created_exposures = 0
    try:
        for definition in DEMO_COMPANIES:
            company = (
                db.query(Company)
                .filter(Company.name == definition["name"])
                .first()
            )
            if company is None:
                company = Company(
                    name=definition["name"],
                    country=definition["country"],
                    base_currency=definition["base_currency"],
                )
                db.add(company)
                db.flush()
                created_companies += 1

            has_exposures = (
                db.query(Exposure)
                .filter(Exposure.company_id == company.id)
                .first()
                is not None
            )
            if has_exposures:
                continue

            for currency, amount, rate, days, hedge in definition["exposures"]:
                db.add(Exposure(
                    company_id=company.id,
                    currency=currency,
                    foreign_amount=amount,
                    current_fx_rate=rate,
                    payment_date=date.today() + timedelta(days=days),
                    hedge_percentage=hedge,
                ))
                created_exposures += 1

        db.commit()
        return created_companies, created_exposures
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    companies, exposures = seed_demo_data()
    print(f"Created {companies} companies and {exposures} exposures.")
