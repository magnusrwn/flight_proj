from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.flight_prediction_sercive import (
    WEATHER_DAILY_FIELDS,
    build_flight_data,
    build_flight_distance,
    build_ml_model_input,
    extract_daily_weather_features,
    get_nested_str,
    match_flight_to_request,
    predict_delay_from_model,
    predict_flight__service,
)
from src.models.base_models import (
    FlightPredictionResponse,
    FuncResponse,
    RequestWithRetryResponse,
    SendFlightRequest,
)


class FakeDuckDbConnection:
    def __init__(self, row):
        self.row = row
        self.closed = False

    def execute(self, _query, _params):
        return self

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


class FlightPredictionServiceTests(unittest.TestCase):
    def make_weather_payload(self, value=1.0):
        return {
            "daily": {
                field: [value]
                for field in WEATHER_DAILY_FIELDS
            }
        }

    def make_flight_data(self):
        return {
            "flight_date": date(2026, 8, 7),
            "origin": "JFK",
            "dest": "LAX",
            "year": 2026,
            "month": 8,
            "day_of_month": 7,
            "day_of_week": 5,
            "pred_dep_time": 900,
            "pred_arr_time": 1230,
            "pred_elapsed_time": 330,
            "fl_distance": 2475,
        }

    def test_get_nested_str__clean_input(self):
        value = get_nested_str(
            {"flight": {"iataNumber": "AA100"}},
            "flight",
            "iataNumber",
        )

        self.assertEqual(value, "AA100")

    def test_get_nested_str__invalid_nested_shape(self):
        self.assertEqual(
            get_nested_str({"flight": "AA100"}, "flight", "iataNumber"),
            "",
        )
        self.assertEqual(
            get_nested_str({"flight": {"iataNumber": 100}}, "flight", "iataNumber"),
            "",
        )

    def test_match_flight_to_request__skips_invalid_payloads(self):
        request = SendFlightRequest(
            depIataCode="JFK",
            destIataCode="LAX",
            date=date(2026, 8, 7),
            flightNumber="AA100",
        )

        response = match_flight_to_request(
            api_data=[
                "invalid",
                {"arrival": "LAX", "flight": {"iataNumber": "AA100"}},
                {
                    "arrival": {"iataCode": "LAX"},
                    "flight": {"iataNumber": "AA100", "icaoNumber": "AAL100"},
                },
            ],
            req_flight=request,
        )

        self.assertTrue(response.ok)
        self.assertIsInstance(response.data, dict)

    def test_build_flight_distance__clean_input(self):
        with patch(
            "services.flight_prediction_sercive.calculate_distance_miles",
            return_value=2475,
        ):
            response = build_flight_distance(
                {
                    "origin_lat": 40.6413,
                    "origin_long": -73.7781,
                    "dest_lat": 33.9416,
                    "dest_long": -118.4085,
                }
            )

        self.assertTrue(response.ok)
        self.assertEqual(response.data, {"fl_distance": 2475})
        self.assertIsInstance(response.data["fl_distance"], int)

    def test_build_flight_distance__invalid_input(self):
        response = build_flight_distance(
            {
                "origin_lat": 120,
                "origin_long": -73.7781,
                "dest_lat": 33.9416,
                "dest_long": -118.4085,
            }
        )

        self.assertFalse(response.ok)
        self.assertEqual(response.code, 400)

    def test_build_flight_distance__missing_input(self):
        response = build_flight_distance(
            {
                "origin_lat": 40.6413,
                "origin_long": -73.7781,
                "dest_lat": 33.9416,
            }
        )

        self.assertFalse(response.ok)
        self.assertEqual(response.code, 500)

    def test_build_flight_data__uses_flight_date_field(self):
        fake_connection = FakeDuckDbConnection(
            (
                "JFK",
                "New York",
                40.6413,
                -73.7781,
                "LAX",
                "Los Angeles",
                33.9416,
                -118.4085,
            )
        )
        request = SendFlightRequest(
            depIataCode="JFK",
            destIataCode="LAX",
            date=date(2026, 8, 7),
            flightNumber="AA100",
        )

        with patch("services.flight_prediction_sercive.ddb.connect", return_value=fake_connection):
            response = build_flight_data(
                sch_dep_time="09:00",
                sch_arr_time="12:30",
                req_flight=request,
            )

        self.assertTrue(response.ok)
        self.assertEqual(response.data["flight_date"], date(2026, 8, 7))
        self.assertNotIn("date", response.data)
        self.assertTrue(fake_connection.closed)

    def test_extract_daily_weather_features__clean_input(self):
        response = extract_daily_weather_features(
            self.make_weather_payload(2.0),
            "origin",
        )

        self.assertTrue(response.ok)
        self.assertEqual(response.data["origin_weather_code"], 2.0)
        self.assertEqual(response.data["origin_pressure_msl_mean"], 2.0)

    def test_extract_daily_weather_features__invalid_input(self):
        response = extract_daily_weather_features(
            {"daily": {"weather_code": []}},
            "origin",
        )

        self.assertFalse(response.ok)
        self.assertEqual(response.code, 502)

    def test_build_ml_model_input__clean_input(self):
        response = build_ml_model_input(
            flight_data=self.make_flight_data(),
            origin_weather_data=self.make_weather_payload(1.0),
            dest_weather_data=self.make_weather_payload(2.0),
        )

        self.assertTrue(response.ok)
        self.assertEqual(response.data["numerical_input"]["fl_distance"], 2475)
        self.assertEqual(response.data["catagorical_input"]["origin"], "JFK")
        self.assertEqual(response.data["numerical_input"]["origin_weather_code"], 1.0)
        self.assertEqual(response.data["numerical_input"]["dest_weather_code"], 2.0)

    def test_build_ml_model_input__missing_flight_data(self):
        flight_data = self.make_flight_data()
        del flight_data["fl_distance"]

        response = build_ml_model_input(
            flight_data=flight_data,
            origin_weather_data=self.make_weather_payload(1.0),
            dest_weather_data=self.make_weather_payload(2.0),
        )

        self.assertFalse(response.ok)
        self.assertEqual(response.code, 500)

    def test_predict_delay_from_model__clean_input(self):
        class FakeModel:
            def predict(self, _model_df):
                return [1]

            def predict_proba(self, _model_df):
                return [[0.2, 0.8]]

        model_input = build_ml_model_input(
            flight_data=self.make_flight_data(),
            origin_weather_data=self.make_weather_payload(1.0),
            dest_weather_data=self.make_weather_payload(2.0),
        )

        with patch("services.flight_prediction_sercive.joblib.load", return_value=FakeModel()):
            response = predict_delay_from_model(model_input.data)

        self.assertTrue(response.ok)
        FlightPredictionResponse(**response.data)
        self.assertEqual(
            response.data,
            {
                "is_significant_delay": True,
                "significant_delay_probability": 0.8,
            },
        )


class FlightPredictionServiceAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_predict_flight_service__invalid_aviation_data_payload(self):
        request = SendFlightRequest(
            depIataCode="JFK",
            destIataCode="LAX",
            date=date(2026, 8, 7),
            flightNumber="AA100",
        )

        with (
            patch(
                "services.flight_prediction_sercive.is_in_table",
                return_value=FuncResponse(ok=True, data=True),
            ),
            patch(
                "services.flight_prediction_sercive.fetch_scheduled_flight_info",
                return_value=RequestWithRetryResponse(success={"data": {"bad": "shape"}}),
            ),
        ):
            response = await predict_flight__service(request)

        self.assertFalse(response.ok)
        self.assertEqual(response.code, 502)
        self.assertEqual(
            response.message,
            "Aviation API scheduled flight data payload was invalid.",
        )


if __name__ == "__main__":
    unittest.main()
