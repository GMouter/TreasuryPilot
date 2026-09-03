from datetime import date, timedelta


def generate_synthetic_outcomes(
    exposure_id: int,
    foreign_amount: float,
    hedge_percentage: float,
    observations: list[dict],
    hedge_cost_annual_rate: float = 0.02,
    horizon_days: int = 30,
):
    if foreign_amount <= 0:
        raise ValueError("Foreign amount must be greater than zero")
    if not 0 <= hedge_percentage <= 100:
        raise ValueError("Hedge percentage must be between 0 and 100")
    if hedge_cost_annual_rate < 0 or horizon_days <= 0:
        raise ValueError("Cost must be non-negative and horizon must be positive")

    ordered = sorted(
        (item for item in observations if item["rate"] > 0),
        key=lambda item: item["date"],
    )
    outcomes = []
    for decision, settlement in zip(ordered, ordered[horizon_days:]):
        decision_date = date.fromisoformat(decision["date"])
        settlement_date = date.fromisoformat(settlement["date"])
        decision_value = foreign_amount * decision["rate"]
        hedge_cost = (
            decision_value
            * hedge_percentage
            / 100
            * hedge_cost_annual_rate
            * (settlement_date - decision_date).days
            / 365
        )
        outcomes.append({
            "exposure_id": exposure_id,
            "decision_date": decision_date,
            "decision_fx_rate": decision["rate"],
            "settlement_date": settlement_date,
            "settlement_fx_rate": settlement["rate"],
            "hedge_percentage": hedge_percentage,
            "hedge_cost": hedge_cost,
        })
    return outcomes
