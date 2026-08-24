import httpx

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/rates",
    tags=["FX Rates"],
)


@router.get("/{currency}/{base_currency}")
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
        }

    url = "https://api.frankfurter.app/latest"

    params = {
        "from": currency,
        "to": base_currency,
    }

    try:
        with httpx.Client(
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            response = client.get(
                url,
                params=params,
            )
           

        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Frankfurter returned HTTP {exc.response.status_code}",
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to FX rate service: {str(exc)}",
        )

    data = response.json()

    rates = data.get("rates", {})

    if base_currency not in rates:
        raise HTTPException(
            status_code=404,
            detail="FX rate not available for this currency pair",
        )

    return {
        "currency": currency,
        "base_currency": base_currency,
        "rate": rates[base_currency],
        "date": data.get("date"),
    }