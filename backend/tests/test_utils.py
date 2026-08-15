from pathlib import Path
import sys
import unittest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.utils import calculate_distance_miles, is_in_table

class UtilsTests(unittest.TestCase):
    def test_calculate_distance_miles__same_location(self):
        distance = calculate_distance_miles(
            origin_lat=40.6413,
            origin_long=-73.7781,
            dest_lat=40.6413,
            dest_long=-73.7781,
        )

        self.assertEqual(distance, 0)
        self.assertIsInstance(distance, int)

    def test_calculate_distance_miles__clean_input(self):
        distance = calculate_distance_miles(
            origin_lat=40.6413,
            origin_long=-73.7781,
            dest_lat=33.9416,
            dest_long=-118.4085,
        )

        self.assertGreater(distance, 2400)
        self.assertLess(distance, 2500)
        self.assertIsInstance(distance, int)

    def test_calculate_distance_miles__invalid_input(self):
        with self.assertRaises(ValueError):
            calculate_distance_miles(
                origin_lat=float("nan"),
                origin_long=-73.7781,
                dest_lat=33.9416,
                dest_long=-118.4085,
            )

    def test_is_in_table__name_err(self):
        r = is_in_table(
            table_name="weather_req_table_ERR_TABLE_NAME",
            column="code",
            airport_code="JFK"
        )
        self.assertFalse(r.ok)

    def test_is_in_table__clean_input(self):
        r = is_in_table(
            table_name="weather_req_table",
            column="code",
            airport_code="JFK"
        )
        self.assertTrue(r.ok)

    def test_is_in_table_correct__input_no_airport(self):
        r = is_in_table(
            table_name="weather_req_table",
            column="code",
            airport_code="LHR"
        )
        self.assertFalse(r.data)
         

if __name__ == '__main__':
    unittest.main()
