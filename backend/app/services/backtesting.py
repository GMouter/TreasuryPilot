from datetime import date, timedelta
from statistics import quantiles

from app.services.hedge_recommendation import calculate_recommendation


def _percentile(values, percentile):
    if len(values) == 1:
        return values[0]
    return quantiles(values, n=100, method="inclusive")[percentile - 1]


def run_historical_backtest(
    foreign_amount: float,
    historical_rates: list[float],
    hedge_policies: tuple[int, ...] = (0, 50, 75, 90),
    hedge_cost_annual_rate: float = 0.02,
    hedge_horizon_days: int = 30,
    overhedge_penalty_annual_rate: float = 0.01,
    risk_appetite_percentage: int = 75,
):
    if foreign_amount <= 0:
        raise ValueError("Foreign amount must be greater than zero")
    if len(historical_rates) < hedge_horizon_days + 1:
        return {
            "available": False,
            "observation_count": len(historical_rates),
            "scenario_count": 0,
            "reason": f"At least {hedge_horizon_days + 1} historical rates are required for a {hedge_horizon_days}-day backtest.",
        }
    if any(not 0 <= policy <= 100 for policy in hedge_policies):
        raise ValueError("Hedge policies must be between 0 and 100")
    if hedge_cost_annual_rate < 0 or overhedge_penalty_annual_rate < 0 or hedge_horizon_days <= 0:
        raise ValueError("Costs must be non-negative and horizon must be positive")
    if not 0 <= risk_appetite_percentage <= 100:
        raise ValueError("Risk appetite must be between 0 and 100")

    rates = [rate for rate in historical_rates if rate > 0]
    scenarios = []
    for decision_rate, settlement_rate in zip(rates, rates[hedge_horizon_days:]):
        gross_change = foreign_amount * (settlement_rate - decision_rate)
        scenarios.append({
            "decision_rate": decision_rate,
            "settlement_rate": settlement_rate,
            "gross_loss": max(gross_change, 0),
        })

    policy_results = []
    for policy in hedge_policies:
        losses = [
            scenario["gross_loss"] * (100 - policy) / 100
            for scenario in scenarios
        ]
        costs = [
            foreign_amount
            * scenario["decision_rate"]
            * policy
            / 100
            * hedge_cost_annual_rate
            * hedge_horizon_days
            / 365
            for scenario in scenarios
        ]
        overhedge_costs = [
            foreign_amount
            * scenario["decision_rate"]
            * max(policy - risk_appetite_percentage, 0)
            / 100
            * overhedge_penalty_annual_rate
            * hedge_horizon_days
            / 365
            for scenario in scenarios
        ]
        total_costs = sorted(
            loss + cost + overhedge_cost
            for loss, cost, overhedge_cost in zip(losses, costs, overhedge_costs)
        )
        losses.sort()
        average_loss = sum(losses) / len(losses)
        average_total_cost = sum(total_costs) / len(total_costs)
        no_hedge_average = sum(item["gross_loss"] for item in scenarios) / len(scenarios)
        policy_results.append({
            "strategy": f"Fixed {policy}% hedge",
            "hedge_percentage": policy,
            "average_loss": average_loss,
            "p95_loss": _percentile(losses, 95),
            "maximum_loss": losses[-1],
            "average_total_cost": average_total_cost,
            "p95_total_cost": _percentile(total_costs, 95),
            "maximum_total_cost": total_costs[-1],
            "hedge_cost_annual_rate": hedge_cost_annual_rate,
            "overhedge_penalty_annual_rate": overhedge_penalty_annual_rate,
            "risk_appetite_percentage": risk_appetite_percentage,
            "loss_reduction_vs_no_hedge": (
                0 if no_hedge_average == 0 else 1 - average_loss / no_hedge_average
            ),
        })

    adaptive_losses = []
    adaptive_total_costs = []
    adaptive_hedges = []
    for scenario in scenarios:
        decision_value = foreign_amount * scenario["decision_rate"]
        recommendation = calculate_recommendation(
            foreign_amount=foreign_amount,
            base_currency_value=decision_value,
            payment_date=date.today() + timedelta(days=30),
            hedge_percentage=0,
            impact_10_percent=decision_value * 0.10,
        )
        adaptive_hedge = recommendation["recommended_hedge_percentage"]
        adaptive_hedges.append(adaptive_hedge)
        adaptive_losses.append(
            scenario["gross_loss"] * (100 - adaptive_hedge) / 100
        )
        adaptive_total_costs.append(
            adaptive_losses[-1]
            + decision_value
            * adaptive_hedge
            / 100
            * hedge_cost_annual_rate
            * hedge_horizon_days
            / 365
            + decision_value
            * max(adaptive_hedge - risk_appetite_percentage, 0)
            / 100
            * overhedge_penalty_annual_rate
            * hedge_horizon_days
            / 365
        )

    adaptive_losses.sort()
    adaptive_total_costs.sort()
    no_hedge_average = sum(item["gross_loss"] for item in scenarios) / len(scenarios)
    adaptive_average = sum(adaptive_losses) / len(adaptive_losses)
    policy_results.append({
        "strategy": "Adaptive rules engine",
        "hedge_percentage": round(sum(adaptive_hedges) / len(adaptive_hedges)),
        "average_loss": adaptive_average,
        "p95_loss": _percentile(adaptive_losses, 95),
        "maximum_loss": adaptive_losses[-1],
        "average_total_cost": sum(adaptive_total_costs) / len(adaptive_total_costs),
        "p95_total_cost": _percentile(adaptive_total_costs, 95),
        "maximum_total_cost": adaptive_total_costs[-1],
        "hedge_cost_annual_rate": hedge_cost_annual_rate,
        "loss_reduction_vs_no_hedge": (
            0 if no_hedge_average == 0 else 1 - adaptive_average / no_hedge_average
        ),
    })

    return {
        "available": True,
        "observation_count": len(rates),
        "scenario_count": len(scenarios),
        "objective": "Expected FX loss plus annualized hedge cost",
        "hedge_horizon_days": hedge_horizon_days,
        "hedge_cost_annual_rate": hedge_cost_annual_rate,
        "overhedge_penalty_annual_rate": overhedge_penalty_annual_rate,
        "risk_appetite_percentage": risk_appetite_percentage,
        "policies": policy_results,
    }


def summarize_backtests(backtests):
    available = [backtest for backtest in backtests if backtest["available"]]
    if not available:
        return {
            "available": False,
            "exposure_count": len(backtests),
            "reason": "No exposure has enough historical data for backtesting.",
        }

    strategy_totals = {}
    for backtest in available:
        for policy in backtest["policies"]:
            strategy = policy["strategy"]
            totals = strategy_totals.setdefault(strategy, {
                "strategy": strategy,
                "exposure_count": 0,
                "average_loss": 0,
                "p95_loss": 0,
                "maximum_loss": 0,
                "average_total_cost": 0,
                "p95_total_cost": 0,
                "maximum_total_cost": 0,
                "loss_reduction_vs_no_hedge": 0,
            })
            totals["exposure_count"] += 1
            totals["average_loss"] += policy["average_loss"]
            totals["p95_loss"] += policy["p95_loss"]
            totals["maximum_loss"] += policy["maximum_loss"]
            totals["average_total_cost"] += policy.get("average_total_cost", policy["average_loss"])
            totals["p95_total_cost"] += policy.get("p95_total_cost", policy["p95_loss"])
            totals["maximum_total_cost"] += policy.get("maximum_total_cost", policy["maximum_loss"])
            totals["loss_reduction_vs_no_hedge"] += policy["loss_reduction_vs_no_hedge"]

    exposure_count = len(available)
    strategies = []
    for totals in strategy_totals.values():
        for key in ("average_loss", "p95_loss", "maximum_loss", "average_total_cost", "p95_total_cost", "maximum_total_cost", "loss_reduction_vs_no_hedge"):
            totals[key] /= exposure_count
        strategies.append(totals)
    strategies.sort(key=lambda strategy: strategy["average_total_cost"])

    return {
        "available": True,
        "exposure_count": len(backtests),
        "backtested_exposure_count": exposure_count,
        "best_strategy": strategies[0]["strategy"],
        "objective": "Lowest average total cost",
        "strategies": strategies,
    }
