from fastapi import FastAPI
from src.models.base_models import SendFlightRequest
from services.flight_prediction_sercive import predict_flight__service

from src.logger_config import configure_logging
configure_logging(__file__)

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.post("/send-flight")
def send_flight_number(body:SendFlightRequest):
    # [X] Add logger at comments thoguhout all funcs here at end

    # [X] compare it to the apirports dataset: 'weather_req_table.codes'
        # [X] if the airportcode is not in it, then throw err
    
    # [] Send request for flight data/ check flight happening 🚧
    
    # [] clean data (things like making up cols... like the time... it must be calculated)

    # [] send request for weather data

    # [] gather response and clean

    # [] Then begin prediction service
        # [] predict with model
    
    response = predict_flight__service(body)
    return response.data