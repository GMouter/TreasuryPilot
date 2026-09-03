from datetime import date

import pytest

from app.services.synthetic_outcomes import generate_synthetic_outcomes


def test_synthetic_outcomes_use_matched_observation_dates():
    observations = [
        {"date": "2026-01-01", "rate": 0.80},
        {"date": "2026-01-31", "rate": 0.82},
        {"date": "2026-03-02", "rate": 0.81},
    ]

    result = generate_synthetic_outcomes(
        exposure_id=16,
        foreign_amount=100_000,
        hedge_percentage=50,
        observations=observations,
        hedge_cost_annual_rate=0.02,
        horizon_days=1,
    )

    assert len(result) == 2
    assert result[0]["decision_date"] == date(2026, 1, 1)
    assert result[0]["settlement_date"] == date(2026, 1, 31)
    assert result[0]["decision_fx_rate"] == 0.80
    assert result[0]["hedge_cost"] == pytest.approx(65.7534)


def test_synthetic_outcomes_return_empty_for_short_history():
    result = generate_synthetic_outcomes(
        exposure_id=16,
        foreign_amount=100_000,
        hedge_percentage=50,
        observations=[{"date": "2026-01-01", "rate": 0.80}],
        horizon_days=30,
    )

    assert result == []
