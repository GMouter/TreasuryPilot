import pytest

from app.services.risk_estimators import (
    build_parallel_estimates,
    calculate_historical_estimate,
)


def test_historical_estimate_converts_adverse_rate_moves_to_losses():
    result = calculate_historical_estimate(
        foreign_amount=100_000,
        current_fx_rate=1.0,
        historical_rates=[1.0, 0.9, 1.1],
    )

    assert result["available"] is True
    assert result["observation_count"] == 3
    assert result["adverse_observation_count"] == 1
    assert result["median_loss"] == pytest.approx(22_222.2222)
    assert result["maximum_loss"] == pytest.approx(22_222.2222)


def test_historical_estimate_reports_sparse_data():
    result = calculate_historical_estimate(100_000, 1.0, [1.0])

    assert result["available"] is False
    assert result["observation_count"] == 1


def test_parallel_estimates_include_deterministic_and_historical_models():
    result = build_parallel_estimates(
        foreign_amount=100_000,
        current_fx_rate=1.0,
        impact_5_percent=5_263.16,
        impact_10_percent=11_111.11,
        historical_rates=[1.0],
    )

    assert result["deterministic_stress"]["10_percent_loss"] == 11_111.11
    assert result["historical_simulation"]["available"] is False
