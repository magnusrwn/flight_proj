from fastapi import FastAPI, HTTPException
from src.models.base_models import FlightPredRequest, FlightPredictionResponse
from services.flight_prediction_sercive import predict_flight__service

from src.logger_config import configure_logging
configure_logging(__file__)

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.post("/predict", response_model=FlightPredictionResponse)
async def send_flight_number(body:FlightPredRequest) -> FlightPredictionResponse:
    response = await predict_flight__service(body)
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
