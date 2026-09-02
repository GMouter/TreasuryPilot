from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.exposure import Exposure
from app.models.company import Company
from app.models.historical_rate import HistoricalRate
from app.services.rates import get_fx_rate, get_historical_fx_rates


router = APIRouter(
    prefix="/rates",
    tags=["FX Rates"],
)


def _store_observations(db, observations, currency, base_currency):
    stored_count = 0
    for observation in observations:
        observed_date = date.fromisoformat(observation["date"])
        stored = (
            db.query(HistoricalRate)
            .filter(
                HistoricalRate.currency == currency,
                HistoricalRate.base_currency == base_currency,
                HistoricalRate.rate_date == observed_date,
            )
            .first()
        )
        if stored is None:
            db.add(HistoricalRate(
                currency=currency,
                base_currency=base_currency,
                rate_date=observed_date,
                rate=observation["rate"],
            ))
            stored_count += 1
        else:
            stored.rate = observation["rate"]
    return stored_count


@router.post("/history/refresh/{company_id}")
def refresh_company_history(
    company_id: int,
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    base_currency = company.base_currency
    currencies = {
        exposure.currency
        for exposure in db.query(Exposure).filter(Exposure.company_id == company_id).all()
    }
    if not currencies:
        return {"company_id": company_id, "currency_count": 0, "observation_count": 0}

    total_observations = 0
    try:
        for currency in currencies:
            observations = get_historical_fx_rates(currency, base_currency)
            _store_observations(db, observations, currency, base_currency)
            total_observations += len(observations)
        db.commit()
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Unable to refresh historical FX rates: {str(error)}",
        )

    return {
        "company_id": company_id,
        "base_currency": base_currency,
        "currency_count": len(currencies),
        "observation_count": total_observations,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/history/{currency}/{base_currency}")
def get_rate_history(
    currency: str,
    base_currency: str = "GBP",
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    try:
        observations = get_historical_fx_rates(
            currency=currency,
            base_currency=base_currency,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve historical FX rates: {str(error)}",
        )

    currency = currency.upper()
    base_currency = base_currency.upper()
    for observation in observations:
        observed_date = date.fromisoformat(observation["date"])
        stored = (
            db.query(HistoricalRate)
            .filter(
                HistoricalRate.currency == currency,
                HistoricalRate.base_currency == base_currency,
                HistoricalRate.rate_date == observed_date,
            )
            .first()
        )
        if stored is None:
            db.add(HistoricalRate(
                currency=currency,
                base_currency=base_currency,
                rate_date=observed_date,
                rate=observation["rate"],
            ))
        else:
            stored.rate = observation["rate"]

    db.commit()
    return {
        "currency": currency,
        "base_currency": base_currency,
        "start_date": start_date or date.today() - timedelta(days=365),
        "end_date": end_date or date.today(),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "observation_count": len(observations),
        "observations": observations,
    }


@router.get("/{currency}/{base_currency}")
def get_rate(
    currency: str,
    base_currency: str = "GBP",
):
    try:
        return get_fx_rate(
            currency=currency,
            base_currency=base_currency,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve FX rate: {str(error)}",
        )