import sys
import unittest
from pathlib import Path

import duckdb


BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from ml.csv_data_pipeline_funcs import (
    CsvTableBuildError,
    create_and_clean_airport_table,
    create_and_clean_flights_table,
    create_weather_req_table,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "ml"


class CsvPipelineIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.con = duckdb.connect(":memory:")

    def tearDown(self) -> None:
        self.con.close()

    def test_clean_flights_table_builds_and_validates(self) -> None:
        response = create_and_clean_flights_table(
            self.con,
            "flight_data_sample",
            FIXTURE_DIR / "flights_valid.csv",
        )

        self.assertIn("Successfully created", response.message)
        self.assertEqual(3, self.con.sql("SELECT COUNT(*) FROM flight_data_sample").fetchone()[0])

    def test_clean_airport_table_builds_and_validates(self) -> None:
        response = create_and_clean_airport_table(
            self.con,
            "airport_data",
            FIXTURE_DIR / "airports_valid.csv",
        )

        self.assertIn("Successfully created", response.message)
        self.assertEqual(3, self.con.sql("SELECT COUNT(*) FROM airport_data").fetchone()[0])

    def test_weather_request_table_builds_with_deduped_rows(self) -> None:
        create_and_clean_flights_table(
            self.con,
            "flight_data_sample",
            FIXTURE_DIR / "flights_valid.csv",
        )
        create_and_clean_airport_table(
            self.con,
            "airport_data",
            FIXTURE_DIR / "airports_valid.csv",
        )

        response = create_weather_req_table(self.con, "flight_data_sample", "airport_data")

        self.assertIn("Successfully created", response.message)
        self.assertEqual(3, self.con.sql("SELECT COUNT(*) FROM weather_req_table").fetchone()[0])

    def test_missing_required_flight_column_fails(self) -> None:
        with self.assertRaises(CsvTableBuildError):
            create_and_clean_flights_table(
                self.con,
                "flight_data_sample",
                FIXTURE_DIR / "flights_missing_number.csv",
            )

    def test_rows_with_null_airport_code_fail_validation(self) -> None:
        with self.assertRaises(CsvTableBuildError):
            create_and_clean_airport_table(
                self.con,
                "airport_data",
                FIXTURE_DIR / "airports_null_code.csv",
            )


if __name__ == "__main__":
    unittest.main()
