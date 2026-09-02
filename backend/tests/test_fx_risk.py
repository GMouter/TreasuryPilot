import pytest

from app.services.fx_risk import calculate_fx_risk


def test_calculates_base_value_stress_and_hedge_amounts():
    result = calculate_fx_risk(
        foreign_amount=900_000,
        current_fx_rate=1.2,
        hedge_percentage=75,
    )

    assert result.base_currency_value == pytest.approx(1_080_000)
    assert result.impact_5_percent == pytest.approx(54_000)
    assert result.impact_10_percent == pytest.approx(108_000)
    assert result.recommended_hedge_amount == pytest.approx(810_000)
    assert result.unhedged_amount == pytest.approx(270_000)


@pytest.mark.parametrize(
    ("foreign_amount", "current_fx_rate", "hedge_percentage"),
    [
        (0, 1.2, 75),
        (100, 0, 75),
        (100, 1.2, -1),
        (100, 1.2, 101),
    ],
)
def test_rejects_invalid_inputs(foreign_amount, current_fx_rate, hedge_percentage):
    with pytest.raises(ValueError):
        calculate_fx_risk(foreign_amount, current_fx_rate, hedge_percentage)
