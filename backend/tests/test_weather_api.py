from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.api.weather_api import WEATHER_DAILY_FIELDS, fetch_weather_info
from src.models.base_models import RequestWithRetryResponse


class WeatherApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_weather_info__requests_model_daily_fields(self):
        mocked_request = AsyncMock(
            return_value=RequestWithRetryResponse(success={"daily": {}})
        )

        with (
            patch("src.api.weather_api.os.getenv", return_value="test-key"),
            patch("src.api.weather_api.request_with_retry", mocked_request),
        ):
            response = await fetch_weather_info(
                lat=40.6413,
                lon=-73.7781,
                date=date(2026, 8, 7),
            )

        self.assertIsNotNone(response.success)
        mocked_request.assert_awaited_once()
        _url, method, params = mocked_request.await_args.args
        self.assertEqual(method, "GET")
        self.assertEqual(params["daily"], ",".join(WEATHER_DAILY_FIELDS))
        self.assertEqual(params["start_date"], "2026-08-07")
        self.assertEqual(params["end_date"], "2026-08-07")
        self.assertEqual(params["latitude"], 40.6413)
        self.assertEqual(params["longitude"], -73.7781)

    async def test_fetch_weather_info__missing_api_key(self):
        with patch("src.api.weather_api.os.getenv", return_value=None):
            response = await fetch_weather_info(
                lat=40.6413,
                lon=-73.7781,
                date=date(2026, 8, 7),
            )

        self.assertIsNotNone(response.error)
        self.assertEqual(response.error.code, 500)
        self.assertEqual(response.error.description, "OPEN_METEO_API_KEY is not configured.")


if __name__ == "__main__":
    unittest.main()
