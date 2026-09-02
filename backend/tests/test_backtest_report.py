from app.services.backtesting import summarize_backtests


def backtest(strategy_values):
    return {
        "available": True,
        "policies": [
            {
                "strategy": name,
                "average_loss": average,
                "p95_loss": average * 2,
                "maximum_loss": average * 3,
                "loss_reduction_vs_no_hedge": reduction,
            }
            for name, average, reduction in strategy_values
        ],
    }


def test_summary_identifies_lowest_average_loss_strategy():
    result = summarize_backtests([
        backtest([
            ("Fixed 50% hedge", 100, 0.5),
            ("Adaptive rules engine", 80, 0.6),
        ]),
        backtest([
            ("Fixed 50% hedge", 120, 0.5),
            ("Adaptive rules engine", 90, 0.6),
        ]),
    ])

    assert result["best_strategy"] == "Adaptive rules engine"
    assert result["strategies"][0]["average_loss"] == 85
    assert result["strategies"][0]["exposure_count"] == 2


def test_summary_reports_when_history_is_unavailable():
    result = summarize_backtests([{
        "available": False,
        "reason": "Not enough history",
    }])

    assert result["available"] is False
    assert result["exposure_count"] == 1
