import random
from datetime import datetime, timezone
from statistics import quantiles


def calculate_historical_estimate(
    foreign_amount: float,
    current_fx_rate: float,
    historical_rates: list[float],
):
    generated_at = datetime.now(timezone.utc).isoformat()
    if foreign_amount <= 0 or current_fx_rate <= 0:
        raise ValueError("Exposure amount and FX rate must be greater than zero")

    if len(historical_rates) < 2:
        return {
            "available": False,
            "observation_count": len(historical_rates),
            "generated_at": generated_at,
            "reason": "At least two historical rates are required.",
        }

    ordered_rates = [rate for rate in historical_rates if rate > 0]
    returns = [
        (current_rate - previous_rate) / previous_rate
        for previous_rate, current_rate in zip(ordered_rates, ordered_rates[1:])
    ]
    adverse_losses = []
    for movement in returns:
        if movement > 0:
            shocked_rate = current_fx_rate * (1 + movement)
            current_value = foreign_amount * current_fx_rate
            shocked_value = foreign_amount * shocked_rate
            adverse_losses.append(shocked_value - current_value)

    if not adverse_losses:
        return {
            "available": True,
            "observation_count": len(ordered_rates),
            "adverse_observation_count": 0,
            "generated_at": generated_at,
            "median_loss": 0,
            "p95_loss": 0,
            "p99_loss": 0,
            "maximum_loss": 0,
        }

    sorted_losses = sorted(adverse_losses)
    if len(sorted_losses) == 1:
        p95_loss = p99_loss = sorted_losses[0]
    else:
        percentile_values = quantiles(sorted_losses, n=100, method="inclusive")
        p95_loss = percentile_values[94]
        p99_loss = percentile_values[98]

    return {
        "available": True,
        "observation_count": len(ordered_rates),
        "adverse_observation_count": len(adverse_losses),
        "median_loss": sorted_losses[len(sorted_losses) // 2],
        "p95_loss": p95_loss,
        "p99_loss": p99_loss,
        "maximum_loss": sorted_losses[-1],
        "generated_at": generated_at,
    }


def calculate_monte_carlo_estimate(
    foreign_amount: float,
    current_fx_rate: float,
    historical_rates: list[float],
    horizon_days: int = 30,
    simulations: int = 5000,
    seed: int | None = None,
):
    generated_at = datetime.now(timezone.utc).isoformat()
    if foreign_amount <= 0 or current_fx_rate <= 0:
        raise ValueError("Exposure amount and FX rate must be greater than zero")
    if horizon_days <= 0 or simulations < 100:
        raise ValueError("Horizon must be positive and simulation count must be at least 100")

    ordered_rates = [rate for rate in historical_rates if rate > 0]
    if len(ordered_rates) < 3:
        return {
            "available": False,
            "observation_count": len(ordered_rates),
            "generated_at": generated_at,
            "reason": "At least three historical rates are required.",
        }

    returns = [
        (current_rate - previous_rate) / previous_rate
        for previous_rate, current_rate in zip(ordered_rates, ordered_rates[1:])
    ]
    generator = random.Random(seed)
    current_value = foreign_amount * current_fx_rate
    losses = []

    for _ in range(simulations):
        simulated_rate = current_fx_rate
        for _ in range(horizon_days):
            simulated_rate *= 1 + generator.choice(returns)
        simulated_value = foreign_amount * simulated_rate
        losses.append(simulated_value - current_value)

    losses.sort()
    percentile_values = quantiles(losses, n=100, method="inclusive")
    return {
        "available": True,
        "observation_count": len(ordered_rates),
        "horizon_days": horizon_days,
        "simulation_count": simulations,
        "median_loss": percentile_values[49],
        "p95_loss": percentile_values[94],
        "p99_loss": percentile_values[98],
        "maximum_loss": losses[-1],
        "loss_probability": sum(loss > 0 for loss in losses) / simulations,
        "generated_at": generated_at,
    }


def build_parallel_estimates(
    foreign_amount: float,
    current_fx_rate: float,
    impact_5_percent: float,
    impact_10_percent: float,
    historical_rates: list[float],
):
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assumptions": {
            "historical_simulation": "Observed adverse daily FX moves are replayed against the current exposure.",
            "monte_carlo": "Observed daily FX returns are sampled with replacement over a 30-day horizon.",
        },
        "deterministic_stress": {
            "5_percent_loss": impact_5_percent,
            "10_percent_loss": impact_10_percent,
        },
        "historical_simulation": calculate_historical_estimate(
            foreign_amount=foreign_amount,
            current_fx_rate=current_fx_rate,
            historical_rates=historical_rates,
        ),
        "monte_carlo": calculate_monte_carlo_estimate(
            foreign_amount=foreign_amount,
            current_fx_rate=current_fx_rate,
            historical_rates=historical_rates,
        ),
    }
