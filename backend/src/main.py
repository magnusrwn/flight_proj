import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.flight_prediction_service import predict_flight_service
from src.logger_config import configure_logging
from src.models.base_models import FlightPredRequest, FlightPredictionResponse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = configure_logging(BACKEND_ROOT / "logs/api.log")
logger = logging.getLogger(__name__)
logger.info("FastAPI logging configured: %s", LOG_FILE)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.post("/predict", response_model=FlightPredictionResponse)
async def send_flight_prediction(body:FlightPredRequest) -> FlightPredictionResponse:
    response = await predict_flight_service(body)
    if not response.ok:
        raise HTTPException(
            status_code=response.code or 500,
            detail=response.data or {
                "code": response.code or 500,
                "description": response.message or "Flight prediction request failed.",
            },
        )
    data:FlightPredictionResponse = response.data
    return data
