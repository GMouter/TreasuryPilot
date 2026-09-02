from datetime import date, timedelta

from app.services.hedge_recommendation import calculate_recommendation


def make_recommendation(hedge_percentage=0, days=30, base_value=1_000_000):
    return calculate_recommendation(
        foreign_amount=base_value,
        base_currency_value=base_value,
        payment_date=date.today() + timedelta(days=days),
        hedge_percentage=hedge_percentage,
        impact_10_percent=base_value * 0.111111,
    )


def test_high_risk_near_term_exposure_recommends_forward_and_hedge():
    result = make_recommendation(hedge_percentage=0, days=30)

    assert result["risk_level"] == "Critical"
    assert result["recommended_hedge_percentage"] == 90
    assert result["instrument"] == "Forward"
    assert result["days_to_payment"] == 30


def test_recommendation_never_reduces_existing_hedge():
    result = make_recommendation(hedge_percentage=95, days=365, base_value=10_000)

    assert result["recommended_hedge_percentage"] == 95
    assert "meets or exceeds" in result["reasons"][0]


def test_long_dated_exposure_uses_layered_hedge():
    result = make_recommendation(hedge_percentage=50, days=365, base_value=100_000)

    assert result["instrument"] == "Layered hedge"
    assert result["recommended_hedge_percentage"] >= 50
