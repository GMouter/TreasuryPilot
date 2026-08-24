from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.exposure import Exposure
from app.services.fx_risk import calculate_fx_risk
from app.services.hedge_recommendation import calculate_recommendation


router = APIRouter(
    prefix="/exposures",
    tags=["Exposures"],
)


class ExposureRequest(BaseModel):
    company_id: int
    currency: str = Field(min_length=3, max_length=3)
    foreign_amount: float = Field(gt=0)
    current_fx_rate: float = Field(gt=0)
    payment_date: date
    hedge_percentage: float = Field(
        default=75.0,
        ge=0,
        le=100,
    )


@router.post("/")
def create_exposure(
    request: ExposureRequest,
    db: Session = Depends(get_db),
):
    exposure = Exposure(
        company_id=request.company_id,
        currency=request.currency.upper(),
        foreign_amount=request.foreign_amount,
        current_fx_rate=request.current_fx_rate,
        payment_date=request.payment_date,
        hedge_percentage=request.hedge_percentage,
    )

    db.add(exposure)
    db.commit()
    db.refresh(exposure)

    risk = calculate_fx_risk(
        foreign_amount=request.foreign_amount,
        current_fx_rate=request.current_fx_rate,
        hedge_percentage=request.hedge_percentage,
    )

    recommendation = calculate_recommendation(
        foreign_amount=request.foreign_amount,
        base_currency_value=risk.base_currency_value,
        payment_date=request.payment_date,
        hedge_percentage=request.hedge_percentage,
        impact_10_percent=risk.impact_10_percent,
    )

    return {
        "id": exposure.id,
        "company_id": exposure.company_id,
        "currency": exposure.currency,
        "foreign_amount": exposure.foreign_amount,
        "payment_date": exposure.payment_date,
        "fx_rate": exposure.current_fx_rate,

        "exposure": {
            "base_currency_value": risk.base_currency_value,
        },

        "stress_test": {
            "5_percent_adverse_move": risk.impact_5_percent,
            "10_percent_adverse_move": risk.impact_10_percent,
        },

        "hedging": {
            "current_hedge_percentage": exposure.hedge_percentage,
            "hedged_amount": risk.recommended_hedge_amount,
            "unhedged_amount": risk.unhedged_amount,
        },

        "recommendation": recommendation,
    }

@router.get("/")
def get_exposures(
    db: Session = Depends(get_db),
):
    exposures = db.query(Exposure).all()

    return exposures



@router.get("/{exposure_id}")
def get_exposure(
    exposure_id: int,
    db: Session = Depends(get_db),
):
    exposure = (
        db.query(Exposure)
        .filter(Exposure.id == exposure_id)
        .first()
    )

    if exposure is None:
        raise HTTPException(
            status_code=404,
            detail="Exposure not found",
        )

    return exposure

@router.get("/summary/{company_id}")
@router.get("/summary/{company_id}")
def get_exposure_summary(
    company_id: int,
    db: Session = Depends(get_db),
):
    exposures = (
        db.query(Exposure)
        .filter(Exposure.company_id == company_id)
        .all()
    )

    if not exposures:
        raise HTTPException(
            status_code=404,
            detail="No exposures found for this company",
        )

    total_base_value = 0
    total_hedged = 0
    total_unhedged = 0
    total_5_percent_risk = 0
    total_10_percent_risk = 0

    # New portfolio-level calculations
    total_recommended_hedge = 0

    currency_totals = {}
    exposure_recommendations = []

    risk_scores = []

    # Track the most important exposure
    priority_exposure = None

    for exposure in exposures:

        risk = calculate_fx_risk(
            foreign_amount=exposure.foreign_amount,
            current_fx_rate=exposure.current_fx_rate,
            hedge_percentage=exposure.hedge_percentage,
        )

        recommendation = calculate_recommendation(
            foreign_amount=exposure.foreign_amount,
            base_currency_value=risk.base_currency_value,
            payment_date=exposure.payment_date,
            hedge_percentage=exposure.hedge_percentage,
            impact_10_percent=risk.impact_10_percent,
        )

        # --------------------------------------------------
        # Portfolio totals
        # --------------------------------------------------

        total_base_value += risk.base_currency_value

        total_hedged += risk.recommended_hedge_amount

        total_unhedged += risk.unhedged_amount

        total_5_percent_risk += risk.impact_5_percent

        total_10_percent_risk += risk.impact_10_percent

        # Recommended hedge for this exposure
        total_recommended_hedge += (
            recommendation["recommended_hedge_amount"]
        )

        risk_scores.append(
            recommendation["risk_score"]
        )

        # --------------------------------------------------
        # Identify highest-priority exposure
        # --------------------------------------------------

        if priority_exposure is None:
            priority_exposure = {
                "exposure_id": exposure.id,
                "currency": exposure.currency,
                "base_currency_value": risk.base_currency_value,
                "risk_score": recommendation["risk_score"],
                "risk_level": recommendation["risk_level"],
                "payment_date": exposure.payment_date,
                "days_to_payment": recommendation["days_to_payment"],
            }

        else:

            current_score = recommendation["risk_score"]
            priority_score = priority_exposure["risk_score"]

            current_days = recommendation["days_to_payment"]
            priority_days = priority_exposure["days_to_payment"]

            # Higher risk takes priority.
            # If risk is equal, earlier payment takes priority.

            if (
                current_score > priority_score
                or (
                    current_score == priority_score
                    and current_days < priority_days
                )
            ):
                priority_exposure = {
                    "exposure_id": exposure.id,
                    "currency": exposure.currency,
                    "base_currency_value": risk.base_currency_value,
                    "risk_score": recommendation["risk_score"],
                    "risk_level": recommendation["risk_level"],
                    "payment_date": exposure.payment_date,
                    "days_to_payment": recommendation["days_to_payment"],
                }

        # --------------------------------------------------
        # Currency totals
        # --------------------------------------------------

        currency = exposure.currency

        if currency not in currency_totals:
            currency_totals[currency] = {
                "foreign_amount": 0,
                "base_currency_value": 0,
            }

        currency_totals[currency]["foreign_amount"] += (
            exposure.foreign_amount
        )

        currency_totals[currency]["base_currency_value"] += (
            risk.base_currency_value
        )

        # --------------------------------------------------
        # Individual recommendation
        # --------------------------------------------------

        exposure_recommendations.append({
            "exposure_id": exposure.id,
            "currency": exposure.currency,
            "foreign_amount": exposure.foreign_amount,
            "base_currency_value": risk.base_currency_value,
            "payment_date": exposure.payment_date,

            "risk_score": recommendation["risk_score"],
            "risk_level": recommendation["risk_level"],

            "recommended_hedge_percentage": (
                recommendation[
                    "recommended_hedge_percentage"
                ]
            ),

            "recommended_hedge_amount": (
                recommendation[
                    "recommended_hedge_amount"
                ]
            ),

            "unhedged_amount": (
                recommendation[
                    "unhedged_amount"
                ]
            ),

            "instrument": recommendation["instrument"],

            "recommended_action": (
                recommendation[
                    "recommended_action"
                ]
            ),

            "recommendation_summary": (
                recommendation[
                    "recommendation_summary"
                ]
            ),

            "potential_10_percent_loss": (
                recommendation[
                    "potential_10_percent_loss"
                ]
            ),

            "days_to_payment": (
                recommendation[
                    "days_to_payment"
                ]
            ),

            "reasons": recommendation["reasons"],
        })

    # --------------------------------------------------
    # Overall portfolio risk score
    # --------------------------------------------------

    overall_risk_score = round(
        sum(risk_scores) / len(risk_scores)
    )

    if overall_risk_score >= 75:
        overall_risk_level = "Critical"

    elif overall_risk_score >= 55:
        overall_risk_level = "High"

    elif overall_risk_score >= 35:
        overall_risk_level = "Moderate"

    else:
        overall_risk_level = "Low"

    # --------------------------------------------------
    # Current hedge coverage
    # --------------------------------------------------

    if total_base_value > 0:
        hedge_coverage = (
            total_hedged
            / total_base_value
            * 100
        )

        recommended_hedge_coverage = (
            total_recommended_hedge
            / total_base_value
            * 100
        )

    else:
        hedge_coverage = 0
        recommended_hedge_coverage = 0

    # --------------------------------------------------
    # Additional hedge required
    # --------------------------------------------------

    additional_hedge_required = max(
        0,
        total_recommended_hedge - total_hedged,
    )

    # --------------------------------------------------
    # Portfolio recommendation
    # --------------------------------------------------

    if additional_hedge_required > 0:

        portfolio_action = (
            f"Increase portfolio hedge coverage to "
            f"approximately "
            f"{recommended_hedge_coverage:.0f}%."
        )

        if priority_exposure:
            portfolio_action += (
                f" Prioritise the "
                f"{priority_exposure['currency']} exposure."
            )

    else:

        portfolio_action = (
            "Current portfolio hedge coverage "
            "meets the model's recommended level."
        )

    # --------------------------------------------------
    # Portfolio summary
    # --------------------------------------------------

    portfolio_summary = (
        f"The portfolio contains {len(exposures)} "
        f"FX exposure(s) with total exposure of "
        f"£{total_base_value:,.0f}. "
        f"Current hedge coverage is "
        f"{hedge_coverage:.0f}%, compared with a "
        f"model recommendation of "
        f"{recommended_hedge_coverage:.0f}%. "
        f"Overall portfolio risk is "
        f"{overall_risk_level.lower()} "
        f"({overall_risk_score}/100)."
    )

    # --------------------------------------------------
    # Return portfolio dashboard
    # --------------------------------------------------

    return {
        "company_id": company_id,

        "portfolio": {
            "total_exposures": len(exposures),

            "total_base_currency_exposure": (
                total_base_value
            ),

            "total_hedged": (
                total_hedged
            ),

            "total_unhedged": (
                total_unhedged
            ),

            "hedge_coverage_percentage": (
                hedge_coverage
            ),

            "recommended_hedge_coverage_percentage": (
                recommended_hedge_coverage
            ),

            "recommended_total_hedge": (
                total_recommended_hedge
            ),

            "additional_hedge_required": (
                additional_hedge_required
            ),
        },

        "risk": {
            "overall_score": (
                overall_risk_score
            ),

            "overall_level": (
                overall_risk_level
            ),

            "5_percent_adverse_move": (
                total_5_percent_risk
            ),

            "10_percent_adverse_move": (
                total_10_percent_risk
            ),
        },

        "portfolio_recommendation": {
            "action": portfolio_action,

            "summary": portfolio_summary,

            "priority_exposure": (
                priority_exposure
            ),
        },

        "currencies": currency_totals,

        "exposures": exposure_recommendations,
    }