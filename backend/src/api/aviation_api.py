from pathlib import Path
import sys
from dotenv import load_dotenv
import os

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
from src.utils import request_with_retry
from src.models.base_models import (
    PresentError,
    FlightPredRequest,
    RequestWithRetryResponse,
)

load_dotenv()

async def fetch_scheduled_flight_info(body:FlightPredRequest) -> RequestWithRetryResponse:
    method = "GET"
    url = "https://api.aviationstack.com/v1/flightsFuture"
    api_key = os.getenv("AVIATION_STACK_API_KEY")

    if not api_key:
        return RequestWithRetryResponse(
            error=PresentError(
                code=500,
                description="AVIATION_STACK_API_KEY is not configured.",
            )
        )

    params = {
        'access_key': api_key,
        'type':'departure',
        'date':body.date,
        'iataCode':body.depIataCode
    }
    return await request_with_retry(url, method, params)
