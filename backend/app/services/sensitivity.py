from datetime import date


def calculate_sensitivity(
    foreign_amount: float,
    current_fx_rate: float,
    current_hedge_percentage: float,
):
    if foreign_amount <= 0 or current_fx_rate <= 0:
        raise ValueError("Exposure amount and FX rate must be greater than zero")
    if not 0 <= current_hedge_percentage <= 100:
        raise ValueError("Hedge percentage must be between 0 and 100")

    current_value = foreign_amount * current_fx_rate
    shocks = []
    for shock in (2, 5, 10, 15):
        shocked_value = foreign_amount * (current_fx_rate * (1 + shock / 100))
        gross_loss = shocked_value - current_value
        shocks.append({
            "shock_percentage": shock,
            "gross_loss": gross_loss,
            "net_loss_at_current_hedge": gross_loss * (100 - current_hedge_percentage) / 100,
        })

    hedge_levels = []
    ten_percent_loss = next(
        scenario["gross_loss"]
        for scenario in shocks
        if scenario["shock_percentage"] == 10
    )
    for hedge_percentage in (0, 50, 75, 90, 100):
        hedge_levels.append({
            "hedge_percentage": hedge_percentage,
            "net_loss_at_10_percent_shock": ten_percent_loss * (100 - hedge_percentage) / 100,
        })

    horizon_scenarios = []
    for days in (30, 90, 180, 365):
        if days <= 90:
            instrument = "Forward"
        elif days <= 180:
            instrument = "Forward or layered hedge"
        else:
            instrument = "Layered hedge"
        horizon_scenarios.append({
            "days_to_payment": days,
            "suggested_instrument": instrument,
        })

    return {
        "current_value": current_value,
        "shock_scenarios": shocks,
        "hedge_scenarios": hedge_levels,
        "payment_horizon_scenarios": horizon_scenarios,
        "generated_on": date.today(),
    }
