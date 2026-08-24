from datetime import date


def calculate_recommendation(
    foreign_amount: float,
    base_currency_value: float,
    payment_date: date,
    hedge_percentage: float,
    impact_10_percent: float,
):
    """
    Generate a rules-based FX hedge recommendation.

    This is an MVP decision-support engine.
    It is not financial advice or a production trading model.
    """

    today = date.today()

    days_to_payment = (payment_date - today).days

    # --------------------------------------------------
    # 1. Exposure size score
    # --------------------------------------------------

    if base_currency_value < 25_000:
        size_score = 10

    elif base_currency_value < 100_000:
        size_score = 20

    elif base_currency_value < 500_000:
        size_score = 30

    elif base_currency_value < 1_000_000:
        size_score = 40

    else:
        size_score = 50

    # --------------------------------------------------
    # 2. Time horizon score
    # --------------------------------------------------

    if days_to_payment < 0:
        time_score = 0

    elif days_to_payment <= 30:
        time_score = 30

    elif days_to_payment <= 90:
        time_score = 25

    elif days_to_payment <= 180:
        time_score = 15

    else:
        time_score = 5

    # --------------------------------------------------
    # 3. Current hedge score
    # --------------------------------------------------

    if hedge_percentage < 25:
        hedge_score = 20

    elif hedge_percentage < 50:
        hedge_score = 15

    elif hedge_percentage < 75:
        hedge_score = 10

    elif hedge_percentage < 90:
        hedge_score = 5

    else:
        hedge_score = 0

    # --------------------------------------------------
    # 4. Stress impact score
    # --------------------------------------------------

    if base_currency_value > 0:
        stress_ratio = (
            impact_10_percent / base_currency_value
        )
    else:
        stress_ratio = 0

    if stress_ratio >= 0.10:
        stress_score = 20

    elif stress_ratio >= 0.07:
        stress_score = 15

    elif stress_ratio >= 0.05:
        stress_score = 10

    else:
        stress_score = 5

    # --------------------------------------------------
    # 5. Total risk score
    # --------------------------------------------------

    raw_score = (
        size_score
        + time_score
        + hedge_score
        + stress_score
    )

    risk_score = min(raw_score, 100)

    # --------------------------------------------------
    # 6. Risk classification
    # --------------------------------------------------

    if risk_score >= 75:
        risk_level = "Critical"

    elif risk_score >= 55:
        risk_level = "High"

    elif risk_score >= 35:
        risk_level = "Moderate"

    else:
        risk_level = "Low"

    # --------------------------------------------------
    # 7. Recommended hedge percentage
    # --------------------------------------------------

    if risk_score >= 75:
        recommended_hedge = 90

    elif risk_score >= 55:
        recommended_hedge = 80

    elif risk_score >= 35:
        recommended_hedge = 65

    else:
        recommended_hedge = 50

    # Never recommend reducing an existing hedge.
    recommended_hedge = max(
        recommended_hedge,
        hedge_percentage,
    )

    # --------------------------------------------------
    # 8. Hedge amounts
    # --------------------------------------------------

    recommended_hedge_amount = (
        base_currency_value
        * recommended_hedge
        / 100
    )

    unhedged_amount = (
        base_currency_value
        * (100 - recommended_hedge)
        / 100
    )

    # --------------------------------------------------
    # 9. Instrument recommendation
    # --------------------------------------------------

    if days_to_payment <= 90:
        instrument = "Forward"

    elif days_to_payment <= 180:
        instrument = "Forward or layered hedge"

    else:
        instrument = "Layered hedge"

    # --------------------------------------------------
    # 10. Primary recommendation
    # --------------------------------------------------

    if risk_level == "Critical":
        recommended_action = (
            f"Increase hedge coverage to "
            f"{recommended_hedge}% using a {instrument.lower()}."
        )

    elif risk_level == "High":
        recommended_action = (
            f"Hedge approximately {recommended_hedge}% "
            f"of the exposure using a {instrument.lower()}."
        )

    elif risk_level == "Moderate":
        recommended_action = (
            f"Consider hedging approximately "
            f"{recommended_hedge}% of the exposure."
        )

    else:
        recommended_action = (
            f"Maintain a partial hedge of approximately "
            f"{recommended_hedge}% and retain flexibility."
        )

    # --------------------------------------------------
    # 11. Recommendation summary
    # --------------------------------------------------

    if days_to_payment < 0:
        timing_description = "Payment date has already passed."

    elif days_to_payment <= 30:
        timing_description = "Payment is due within 30 days."

    elif days_to_payment <= 90:
        timing_description = "Payment is due within 90 days."

    elif days_to_payment <= 180:
        timing_description = "Payment is due within 6 months."

    else:
        timing_description = "Payment is more than 6 months away."

    recommendation_summary = (
        f"{recommended_action} "
        f"The exposure is currently assessed as "
        f"{risk_level.lower()} FX risk with a score of "
        f"{risk_score}/100. "
        f"{timing_description}"
    )

    # --------------------------------------------------
    # 12. Explanation
    # --------------------------------------------------

    reasons = []

    if base_currency_value >= 500_000:
        reasons.append(
            "The exposure is large relative to the portfolio."
        )

    elif base_currency_value >= 100_000:
        reasons.append(
            "The exposure is material and could have a "
            "meaningful impact on cash flows."
        )

    if days_to_payment <= 90:
        reasons.append(
            "The payment is due within 90 days, reducing "
            "the time available to absorb an adverse FX move."
        )

    elif days_to_payment <= 180:
        reasons.append(
            "The payment is due within six months, creating "
            "a meaningful period of FX uncertainty."
        )

    if hedge_percentage < recommended_hedge:
        reasons.append(
            f"Current hedge coverage of {hedge_percentage:.0f}% "
            f"is below the model's recommended "
            f"{recommended_hedge}%."
        )

    elif hedge_percentage >= recommended_hedge:
        reasons.append(
            "Current hedge coverage already meets or exceeds "
            "the model's recommended level."
        )

    if stress_ratio >= 0.07:
        reasons.append(
            "A 10% adverse FX movement would create a "
            "significant financial impact."
        )

    elif stress_ratio >= 0.05:
        reasons.append(
            "The exposure has a meaningful sensitivity to "
            "adverse FX movements."
        )

    if recommended_hedge < 90:
        reasons.append(
            f"Leaving approximately "
            f"{100 - recommended_hedge}% unhedged preserves "
            "some flexibility if the underlying payment "
            "amount or timing changes."
        )

    # Fallback explanation
    if not reasons:
        reasons.append(
            "The exposure currently presents relatively "
            "limited FX risk."
        )

    # --------------------------------------------------
    # 13. Return recommendation
    # --------------------------------------------------

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,

        "recommended_hedge_percentage": (
            recommended_hedge
        ),

        "recommended_hedge_amount": (
            recommended_hedge_amount
        ),

        "unhedged_amount": (
            unhedged_amount
        ),

        "instrument": instrument,

        "recommended_action": (
            recommended_action
        ),

        "recommendation_summary": (
            recommendation_summary
        ),

        "days_to_payment": (
            days_to_payment
        ),

        "potential_10_percent_loss": (
            impact_10_percent
        ),

        "reasons": reasons,
    }