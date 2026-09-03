from datetime import date

import pytest
from pydantic import ValidationError

from app.routers.exposures import OutcomeImportItem
from app.services.outcome_evaluation import evaluate_outcomes


def test_outcome_import_item_accepts_realized_settlement_data():
    item = OutcomeImportItem(
        exposure_id=16,
        decision_date=date(2026, 1, 2),
        decision_fx_rate=0.79,
        settlement_date=date(2026, 2, 1),
        settlement_fx_rate=0.82,
        hedge_percentage=75,
        hedge_cost=125.50,
    )

    assert item.exposure_id == 16
    assert item.settlement_fx_rate == 0.82
    assert item.hedge_cost == 125.50


@pytest.mark.parametrize("field", ["decision_fx_rate", "settlement_fx_rate"])
def test_outcome_import_item_rejects_non_positive_rates(field):
    values = {
        "exposure_id": 16,
        "decision_date": date(2026, 1, 2),
        "decision_fx_rate": 0.79,
        "settlement_date": date(2026, 2, 1),
        "settlement_fx_rate": 0.82,
        "hedge_percentage": 75,
        "hedge_cost": 0,
    }
    values[field] = 0

    with pytest.raises(ValidationError):
        OutcomeImportItem(**values)


def test_evaluation_compares_realized_cost_with_no_hedge():
    outcome = type("Outcome", (), {
        "exposure_id": 16,
        "decision_fx_rate": 0.80,
        "settlement_fx_rate": 0.84,
        "hedge_percentage": 75,
        "hedge_cost": 100,
    })()

    result = evaluate_outcomes([outcome], {16: 100_000})

    assert result["available"] is True
    assert result["outcome_count"] == 1
    assert result["strategies"][-1]["strategy"] == "No hedge"
    assert result["strategies"][-1]["average_total_cost"] == pytest.approx(4_000)
