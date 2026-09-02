from datetime import date, timedelta

import httpx


def get_fx_rate(
    currency: str,
    base_currency: str = "GBP",
):
    currency = currency.upper()
    base_currency = base_currency.upper()

    if currency == base_currency:
        return {
            "currency": currency,
            "base_currency": base_currency,
            "rate": 1.0,
            "date": None,
        }

    url = "https://api.frankfurter.app/latest"

    params = {
        "from": currency,
        "to": base_currency,
    }

    with httpx.Client(
        timeout=10.0,
        follow_redirects=True,
    ) as client:
        response = client.get(
            url,
            params=params,
        )

    response.raise_for_status()

    data = response.json()

    rates = data.get("rates", {})

    if base_currency not in rates:
        raise ValueError(
            "FX rate not available for this currency pair"
        )

    return {
        "currency": currency,
        "base_currency": base_currency,
        "rate": rates[base_currency],
        "date": data.get("date"),
    }


def get_historical_fx_rates(
    currency: str,
    base_currency: str = "GBP",
    start_date: date | None = None,
    end_date: date | None = None,
):
    currency = currency.upper()
    base_currency = base_currency.upper()
    end_date = end_date or date.today()
    start_date = start_date or end_date - timedelta(days=365)

    if start_date > end_date:
        raise ValueError("Start date must be before end date")

    if currency == base_currency:
        return [{
            "currency": currency,
            "base_currency": base_currency,
            "rate": 1.0,
            "date": day.isoformat(),
        } for day in (start_date, end_date)]

    url = f"https://api.frankfurter.app/{start_date}..{end_date}"
    params = {"from": currency, "to": base_currency}

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(url, params=params)

    response.raise_for_status()
    data = response.json()
    observations = []
    for observed_date, rates in data.get("rates", {}).items():
        if base_currency in rates:
            observations.append({
                "currency": currency,
                "base_currency": base_currency,
                "rate": rates[base_currency],
                "date": observed_date,
            })

    if not observations:
        raise ValueError("Historical FX rates not available for this currency pair")

    return observations