from fastapi import FastAPI
from sqlalchemy import text

from app.database.database import engine

app = FastAPI(
    title="TreasuryPilot API",
    version="0.1.0"
)

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