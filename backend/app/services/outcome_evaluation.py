def evaluate_outcomes(outcomes, foreign_amounts):
    if not outcomes:
        return {
            "available": False,
            "outcome_count": 0,
            "reason": "No realized outcomes have been imported.",
        }

    realized_costs = []
    no_hedge_costs = []
    policy_costs = {policy: [] for policy in (50, 75, 90)}
    total_hedge_cost = 0.0

    for outcome in outcomes:
        amount = foreign_amounts[outcome.exposure_id]
        gross_loss = max(
            amount * (outcome.settlement_fx_rate - outcome.decision_fx_rate),
            0,
        )
        realized_cost = (
            gross_loss * (100 - outcome.hedge_percentage) / 100
            + outcome.hedge_cost
        )
        realized_costs.append(realized_cost)
        no_hedge_costs.append(gross_loss)
        total_hedge_cost += outcome.hedge_cost

        for policy in policy_costs:
            policy_costs[policy].append(
                gross_loss * (100 - policy) / 100
                + outcome.hedge_cost * policy / max(outcome.hedge_percentage, 1)
            )

    average_no_hedge = sum(no_hedge_costs) / len(no_hedge_costs)
    average_realized = sum(realized_costs) / len(realized_costs)
    strategies = [{
        "strategy": "Executed hedge",
        "average_total_cost": average_realized,
        "maximum_total_cost": max(realized_costs),
        "cost_reduction_vs_no_hedge": (
            0 if average_no_hedge == 0 else 1 - average_realized / average_no_hedge
        ),
    }]

    for policy, costs in policy_costs.items():
        average_cost = sum(costs) / len(costs)
        strategies.append({
            "strategy": f"Counterfactual {policy}% hedge",
            "average_total_cost": average_cost,
            "maximum_total_cost": max(costs),
            "cost_reduction_vs_no_hedge": (
                0 if average_no_hedge == 0 else 1 - average_cost / average_no_hedge
            ),
        })

    strategies.append({
        "strategy": "No hedge",
        "average_total_cost": average_no_hedge,
        "maximum_total_cost": max(no_hedge_costs),
        "cost_reduction_vs_no_hedge": 0,
    })
    strategies.sort(key=lambda strategy: strategy["average_total_cost"])

    return {
        "available": True,
        "outcome_count": len(outcomes),
        "average_executed_hedge_percentage": sum(
            outcome.hedge_percentage for outcome in outcomes
        ) / len(outcomes),
        "total_hedge_cost": total_hedge_cost,
        "best_strategy": strategies[0]["strategy"],
        "strategies": strategies,
    }
