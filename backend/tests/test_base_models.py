from pathlib import Path
import sys
import unittest
from typing import Any
from pydantic import BaseModel, ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.models.base_models import (
    FlightDistanceRequest,
    FlightDistanceResponse,
    FlightPredictionResponse,
    MLModelNumericInput,
    SendFlightRequest,
)


class BaseModelError(Exception):
    """Base exception for pydantic BaseModel faliures"""
class BaseModelFieldCountError(BaseModelError):
    """Raised when field count exceeds the number of fields in the BaseModel"""

# Helper funcs
def collect_schema_path(item, paths=None, path="") -> set[str]:
    '''
    Reccursively searches handed-in data
    returning a set of all paths/ ends to the data
    '''
    if paths == None:
        paths = set()

    if isinstance(item, dict):
        for key, child in item.items():
            dict_path = f"{path}.{key}" if path else key
            paths.add(dict_path)
            collect_schema_path(child, paths, dict_path)

    elif isinstance(item, list):
        list_path = f"{path}[]"
        paths.add(list_path)
        for i in item:
            collect_schema_path(i, paths, list_path)
    return paths

def collect_model_path(model: type[BaseModel], paths=None, path="") -> set[str]:
    if paths == None:
        paths = set()

    for f_name, f_info in model.model_fields.items():
        model_path = f"{path}.{f_name}" if path else f_name
        paths.add(model_path)

        f_type = f_info.annotation
        if isinstance(f_type, type) and issubclass(f_type, BaseModel):
            collect_model_path(model=f_info, paths=paths, path=model_path)
    return paths

def test_field_numbers(schema:list[dict[str, Any]], base_model:type[BaseModel]) -> None:
    schema_explored_set = collect_schema_path(item=schema)
    model_explored_set = collect_model_path(model=base_model)

    if len(schema_explored_set) != len(model_explored_set):
        raise BaseModelFieldCountError

def test_schema_fields(schema:list[dict[str, Any]], base_model:type[BaseModel]):
    for i in schema:
        base_model(**i)

# Test
class BaseModelTests(unittest.TestCase):
    def test_field_count(self) -> None:
        schema = [
            {"depIataCode":"EDI","data":"2026-08-29"},
        ]

        with self.assertRaises(BaseModelFieldCountError):
            test_field_numbers(schema, SendFlightRequest)

    def test_fields(self) -> None:
        schema = [
            {"depIataCode":"EDI", "date":"2026-08-29", "car":"no"},
            {"depIataCode":"LYS", "date":"2026-08-29"}
        ]

        with self.assertRaises(ValidationError) as ctx:
            test_schema_fields(schema, SendFlightRequest)

        # Uncomment when you want to test for specific errs
        # errors = ctx.exception.errors()
        # self.assertEqual(errors[0]["loc"], ("car",))

    def test_flight_distance_request__clean_input(self) -> None:
        model = FlightDistanceRequest(
            origin_lat=40.6413,
            origin_long=-73.7781,
            dest_lat=33.9416,
            dest_long=-118.4085,
        )

        self.assertEqual(model.origin_lat, 40.6413)

    def test_flight_distance_request__invalid_coordinate(self) -> None:
        with self.assertRaises(ValidationError):
            FlightDistanceRequest(
                origin_lat=120,
                origin_long=-73.7781,
                dest_lat=33.9416,
                dest_long=-118.4085,
            )

    def test_flight_distance_response__requires_int_distance(self) -> None:
        model = FlightDistanceResponse(fl_distance=2475)

        self.assertEqual(model.fl_distance, 2475)
        self.assertIsInstance(model.fl_distance, int)

    def test_flight_prediction_response__clean_input(self) -> None:
        model = FlightPredictionResponse(
            is_significant_delay=True,
            significant_delay_probability=0.8,
        )

        self.assertTrue(model.is_significant_delay)
        self.assertEqual(model.significant_delay_probability, 0.8)

    def test_flight_prediction_response__rejects_invalid_contract(self) -> None:
        with self.assertRaises(ValidationError):
            FlightPredictionResponse(
                is_significant_delay=False,
                significant_delay_probability=1.2,
            )

        with self.assertRaises(ValidationError):
            FlightPredictionResponse(
                is_significant_delay=False,
                significant_delay_probability=0.2,
                extra_field="not allowed",
            )

    def test_ml_numeric_input__requires_fl_distance(self) -> None:
        input_data = {
            "year": 2026,
            "month": 8,
            "day_of_month": 7,
            "day_of_week": 5,
            "pred_dep_time": 900,
            "pred_arr_time": 1130,
            "pred_elapsed_time": 330,
            "origin_weather_code": 1.0,
            "origin_apparent_temperature_max": 20.0,
            "origin_temperature_2m_max": 20.0,
            "origin_temperature_2m_min": 10.0,
            "origin_apparent_temperature_min": 10.0,
            "origin_precipitation_sum": 0.0,
            "origin_rain_sum": 0.0,
            "origin_showers_sum": 0.0,
            "origin_snowfall_sum": 0.0,
            "origin_cloud_cover_mean": 50.0,
            "origin_wind_speed_10m_max": 10.0,
            "origin_wind_gusts_10m_max": 15.0,
            "origin_wind_direction_10m_dominant": 180.0,
            "origin_pressure_msl_mean": 1010.0,
            "dest_weather_code": 1.0,
            "dest_temperature_2m_max": 20.0,
            "dest_temperature_2m_min": 10.0,
            "dest_apparent_temperature_max": 20.0,
            "dest_apparent_temperature_min": 10.0,
            "dest_precipitation_sum": 0.0,
            "dest_rain_sum": 0.0,
            "dest_showers_sum": 0.0,
            "dest_snowfall_sum": 0.0,
            "dest_cloud_cover_mean": 50.0,
            "dest_wind_speed_10m_max": 10.0,
            "dest_wind_gusts_10m_max": 15.0,
            "dest_wind_direction_10m_dominant": 180.0,
            "dest_pressure_msl_mean": 1010.0,
        }

        with self.assertRaises(ValidationError):
            MLModelNumericInput(**input_data)

        input_data["fl_distance"] = 2475
        model = MLModelNumericInput(**input_data)
        self.assertEqual(model.fl_distance, 2475)


if __name__ == '__main__':
    unittest.main()
