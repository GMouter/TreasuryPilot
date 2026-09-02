import pytest

from app.services.backtesting import run_historical_backtest


def test_backtest_compares_hedge_policies_against_realized_moves():
    result = run_historical_backtest(
        foreign_amount=100_000,
        historical_rates=[0.80] * 30 + [0.82, 0.81, 0.85],
    )

    assert result["available"] is True
    assert result["scenario_count"] == 3
    assert result["policies"][0]["hedge_percentage"] == 0
    assert result["policies"][0]["average_loss"] == pytest.approx(2_666.6667)
    assert result["policies"][1]["average_loss"] == pytest.approx(1_333.3333)
    assert result["policies"][1]["loss_reduction_vs_no_hedge"] == pytest.approx(0.5)
    assert result["policies"][-1]["strategy"] == "Adaptive rules engine"
    assert 0 <= result["policies"][-1]["hedge_percentage"] <= 100
    assert result["policies"][0]["average_total_cost"] == result["policies"][0]["average_loss"]
    assert result["policies"][1]["average_total_cost"] > result["policies"][1]["average_loss"]


def test_cost_aware_objective_can_prefer_lower_hedge_policy():
    result = run_historical_backtest(
        foreign_amount=100_000,
        historical_rates=[0.80] * 30 + [0.8001, 0.7999],
        hedge_cost_annual_rate=0.20,
    )

    assert result["objective"] == "Expected FX loss plus annualized hedge cost"
    assert result["policies"][0]["average_total_cost"] < result["policies"][1]["average_total_cost"]


def test_overhedge_penalty_increases_cost_above_risk_appetite():
    result = run_historical_backtest(
        foreign_amount=100_000,
        historical_rates=[0.80] * 31,
        overhedge_penalty_annual_rate=0.10,
        risk_appetite_percentage=75,
    )

    fixed_75 = next(item for item in result["policies"] if item["hedge_percentage"] == 75)
    fixed_90 = next(item for item in result["policies"] if item["hedge_percentage"] == 90)
    assert fixed_90["average_total_cost"] > fixed_75["average_total_cost"]


def test_backtest_handles_insufficient_history():
    result = run_historical_backtest(100_000, [0.80])

    assert result["available"] is False
    assert result["scenario_count"] == 0


def test_backtest_rejects_invalid_policy():
    with pytest.raises(ValueError):
        run_historical_backtest(100_000, [0.8] * 31, hedge_policies=(110,))
