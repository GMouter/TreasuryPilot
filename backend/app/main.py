from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database.database import engine
from app.database.base import Base

from app.models.company import Company
from app.models.exposure import Exposure
from app.models.historical_rate import HistoricalRate
from app.models.outcome import ExposureOutcome

from app.routers.companies import router as companies_router
from app.routers.fx_risk import router as fx_risk_router
from app.routers.exposures import router as exposures_router
from app.routers.rates import router as rates_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="TreasuryPilot API",
    version="0.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(companies_router)
app.include_router(fx_risk_router)
app.include_router(exposures_router)
app.include_router(rates_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to TreasuryPilot API"
    }


@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "Database Connected"
    }