from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.fx_risk import calculate_fx_risk


router = APIRouter(
    prefix="/fx-risk",
    tags=["FX Risk"],
)


class FXRiskRequest(BaseModel):
    foreign_amount: float = Field(gt=0)
    current_fx_rate: float = Field(gt=0)
    hedge_percentage: float = Field(
        default=75.0,
        ge=0,
        le=100,
    )


@router.post("/calculate")
def calculate_risk(request: FXRiskRequest):

    try:
        result = calculate_fx_risk(
            foreign_amount=request.foreign_amount,
            current_fx_rate=request.current_fx_rate,
            hedge_percentage=request.hedge_percentage,
        )

        return {
            "foreign_amount": result.foreign_amount,
            "current_fx_rate": result.current_fx_rate,
            "base_currency_value": result.base_currency_value,
            "potential_impact": {
                "5_percent_adverse_move": result.impact_5_percent,
                "10_percent_adverse_move": result.impact_10_percent,
            },
            "hedging": {
                "recommended_percentage": result.recommended_hedge_percentage,
                "hedged_amount": result.recommended_hedge_amount,
                "unhedged_amount": result.unhedged_amount,
            },
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )