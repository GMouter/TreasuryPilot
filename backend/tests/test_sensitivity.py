import pytest

from app.services.sensitivity import calculate_sensitivity


def test_sensitivity_returns_shock_and_hedge_scenarios():
    result = calculate_sensitivity(100_000, 1.0, 75)

    assert result["current_value"] == 100_000
    assert [item["shock_percentage"] for item in result["shock_scenarios"]] == [2, 5, 10, 15]
    assert result["shock_scenarios"][2]["gross_loss"] == pytest.approx(10_000)
    assert result["shock_scenarios"][2]["net_loss_at_current_hedge"] == pytest.approx(2_500)
    assert result["hedge_scenarios"][-1]["net_loss_at_10_percent_shock"] == 0


def test_sensitivity_includes_payment_horizon_guidance():
    result = calculate_sensitivity(100_000, 1.0, 50)

    assert result["payment_horizon_scenarios"][0]["suggested_instrument"] == "Forward"
    assert result["payment_horizon_scenarios"][-1]["suggested_instrument"] == "Layered hedge"


@pytest.mark.parametrize("hedge_percentage", [-1, 101])
def test_sensitivity_rejects_invalid_hedge_percentage(hedge_percentage):
    with pytest.raises(ValueError):
        calculate_sensitivity(100_000, 1.0, hedge_percentage)
