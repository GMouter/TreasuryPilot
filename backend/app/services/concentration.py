def calculate_concentration(exposures):
    totals = {}
    total_base_value = 0.0

    for exposure in exposures:
        base_value = exposure.foreign_amount * exposure.current_fx_rate
        totals[exposure.currency] = totals.get(exposure.currency, 0) + base_value
        total_base_value += base_value

    if total_base_value == 0:
        return {
            "total_base_currency_exposure": 0,
            "currency_count": 0,
            "top_currency": None,
            "top_currency_share": 0,
            "hhi": 0,
            "level": "Low",
            "currencies": [],
        }

    currencies = [
        {
            "currency": currency,
            "base_currency_value": value,
            "share_percentage": value / total_base_value * 100,
        }
        for currency, value in totals.items()
    ]
    currencies.sort(key=lambda item: item["base_currency_value"], reverse=True)
    shares = [item["share_percentage"] / 100 for item in currencies]
    hhi = sum(share * share for share in shares)
    top_share = currencies[0]["share_percentage"]

    if top_share >= 75 or hhi >= 0.60:
        level = "High"
    elif top_share >= 50 or hhi >= 0.35:
        level = "Moderate"
    else:
        level = "Low"

    return {
        "total_base_currency_exposure": total_base_value,
        "currency_count": len(currencies),
        "top_currency": currencies[0]["currency"],
        "top_currency_share": top_share,
        "hhi": hhi,
        "level": level,
        "currencies": currencies,
    }
