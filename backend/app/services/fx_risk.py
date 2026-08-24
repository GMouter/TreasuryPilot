from dataclasses import dataclass


@dataclass
class FXRiskResult:
    foreign_amount: float
    current_fx_rate: float
    base_currency_value: float

    impact_5_percent: float
    impact_10_percent: float

    recommended_hedge_percentage: float
    recommended_hedge_amount: float
    unhedged_amount: float


def calculate_fx_risk(
    foreign_amount: float,
    current_fx_rate: float,
    hedge_percentage: float = 75.0,
) -> FXRiskResult:

    if foreign_amount <= 0:
        raise ValueError("Foreign amount must be greater than zero")

    if current_fx_rate <= 0:
        raise ValueError("FX rate must be greater than zero")

    if not 0 <= hedge_percentage <= 100:
        raise ValueError("Hedge percentage must be between 0 and 100")

    # Convert foreign currency exposure into base currency.
    base_currency_value = foreign_amount / current_fx_rate

    # Calculate potential FX impact from adverse movements.
    value_after_5_percent_move = (
        foreign_amount / (current_fx_rate * 0.95)
    )

    value_after_10_percent_move = (
        foreign_amount / (current_fx_rate * 0.90)
    )

    impact_5_percent = (
        value_after_5_percent_move - base_currency_value
    )

    impact_10_percent = (
        value_after_10_percent_move - base_currency_value
    )

    # Calculate hedge amounts.
    recommended_hedge_amount = (
        base_currency_value * hedge_percentage / 100
    )

    unhedged_amount = (
        base_currency_value - recommended_hedge_amount
    )

    return FXRiskResult(
        foreign_amount=foreign_amount,
        current_fx_rate=current_fx_rate,
        base_currency_value=base_currency_value,
        impact_5_percent=impact_5_percent,
        impact_10_percent=impact_10_percent,
        recommended_hedge_percentage=hedge_percentage,
        recommended_hedge_amount=recommended_hedge_amount,
        unhedged_amount=unhedged_amount,
    )