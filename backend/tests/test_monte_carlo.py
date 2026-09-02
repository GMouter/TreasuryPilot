import pytest

from app.services.risk_estimators import calculate_monte_carlo_estimate


def test_monte_carlo_estimate_is_reproducible():
    arguments = {
        "foreign_amount": 100_000,
        "current_fx_rate": 1.0,
        "historical_rates": [1.0, 0.98, 1.01, 0.97, 1.02],
        "horizon_days": 10,
        "simulations": 500,
        "seed": 42,
    }

    first = calculate_monte_carlo_estimate(**arguments)
    second = calculate_monte_carlo_estimate(**arguments)

    assert {
        key: value for key, value in first.items() if key != "generated_at"
    } == {
        key: value for key, value in second.items() if key != "generated_at"
    }
    assert first["available"] is True
    assert first["simulation_count"] == 500
    assert 0 <= first["loss_probability"] <= 1
    assert first["p99_loss"] >= first["median_loss"]


def test_monte_carlo_reports_insufficient_history():
    result = calculate_monte_carlo_estimate(100_000, 1.0, [1.0, 1.01])

    assert result["available"] is False
    assert result["observation_count"] == 2


@pytest.mark.parametrize("horizon_days", [0, -1])
def test_monte_carlo_rejects_invalid_horizon(horizon_days):
    with pytest.raises(ValueError):
        calculate_monte_carlo_estimate(
            100_000,
            1.0,
            [1.0, 1.01, 0.99],
            horizon_days=horizon_days,
        )
