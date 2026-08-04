from pathlib import Path
import sys
from dotenv import load_dotenv
import os
from datetime import datetime

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
from src.utils import request_with_retry
from src.models.base_models import SendFlightRequest

load_dotenv()

async def fetch_scheduled_flight_info(body:SendFlightRequest)->bool:
    method = "GET"
    url = "https://api.aviationstack.com/v1/flights"
    params = {
        'access_key': os.getenv("AVIATION_STACK_API_KEY"),
        'type':'departure',
        'date':body.date,
        'iataCode':body.depIataCode
    }
    return await request_with_retry(url, method, params)
