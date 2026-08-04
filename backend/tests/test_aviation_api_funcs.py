from pathlib import Path
import sys
import unittest
from datetime import datetime, timedelta

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.api.aviation_api import fetch_scheduled_flight_info
from src.models.base_models import SendFlightRequest

class AviationTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_scheduled_flight_info_date_long(self):
        date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

        r = await fetch_scheduled_flight_info(SendFlightRequest(
            depIataCode="PHX",
            date=date
        ))
        self.assertTrue("success", r)

if __name__ == '__main__':
    unittest.main()