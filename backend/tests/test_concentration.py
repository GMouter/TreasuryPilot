from types import SimpleNamespace

import pytest

from app.services.concentration import calculate_concentration


def exposure(currency, foreign_amount, current_fx_rate=1.0):
    return SimpleNamespace(
        currency=currency,
        foreign_amount=foreign_amount,
        current_fx_rate=current_fx_rate,
    )


def test_concentration_identifies_dominant_currency():
    result = calculate_concentration([
        exposure("USD", 800_000),
        exposure("EUR", 200_000),
    ])

    assert result["top_currency"] == "USD"
    assert result["top_currency_share"] == 80
    assert result["level"] == "High"
    assert result["hhi"] == pytest.approx(0.68)


def test_balanced_portfolio_has_low_concentration():
    result = calculate_concentration([
        exposure("USD", 250_000),
        exposure("EUR", 250_000),
        exposure("JPY", 250_000),
        exposure("CHF", 250_000),
    ])

    assert result["currency_count"] == 4
    assert result["top_currency_share"] == 25
    assert result["level"] == "Low"


def test_empty_portfolio_has_zero_concentration():
    result = calculate_concentration([])

    assert result["level"] == "Low"
    assert result["top_currency"] is None
    assert result["currencies"] == []
