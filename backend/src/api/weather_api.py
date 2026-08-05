from dotenv import load_dotenv
import os
from datetime import date
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
from src.models.base_models import PresentError, RequestWithRetryResponse
from src.utils import request_with_retry

load_dotenv()

async def fetch_weather_info(lat:float, lon:float, date:date) -> RequestWithRetryResponse:
    method = "GET"
    url = "https://customer-api.open-meteo.com/v1/forecast"
    api_key = os.getenv("OPEN_METEO_API_KEY")

    if not api_key:
        return RequestWithRetryResponse(
            error=PresentError(
                code=500,
                description="OPEN_METEO_API_KEY is not configured.",
            )
        )

    params = {
        "apikey": api_key,
        "latitude": lat,
        "longitude": lon,
        "start_date": date.isoformat(),
        "end_date": date.isoformat(),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_sum",
                "rain_sum",
                "showers_sum",
                "snowfall_sum",
                "cloud_cover_mean",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
                "pressure_msl_mean",
            ]
        ),
        "timezone": "auto",
    }

    return await request_with_retry(url, method, params)
