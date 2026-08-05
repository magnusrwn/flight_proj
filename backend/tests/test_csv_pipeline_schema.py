import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.ml.csv_data_pipeline_funcs import TableSchemaMismatchError, _validate_table_schema
from src.models.base_models import CleanedFlightDuckDBTableCols


class SchemaValidationTests(unittest.TestCase):
    def test_matching_schema_passes(self) -> None:
        schema = [
            {"column_name": "date", "column_type": "DATE"},
            {"column_name": "flight_number", "column_type": "DOUBLE"},
            {"column_name": "origin", "column_type": "VARCHAR"},
            {"column_name": "origin_city_name", "column_type": "VARCHAR"},
            {"column_name": "dest", "column_type": "VARCHAR"},
            {"column_name": "dest_city_name", "column_type": "VARCHAR"},
            {"column_name": "pred_dep_time", "column_type": "BIGINT"},
            {"column_name": "pred_arr_time", "column_type": "BIGINT"},
            {"column_name": "pred_elapsed_time", "column_type": "DOUBLE"},
            {"column_name": "distance", "column_type": "DOUBLE"},
            {"column_name": "total_delay", "column_type": "DOUBLE"},
        ]

        _validate_table_schema("flight_data", schema, CleanedFlightDuckDBTableCols)

    def test_missing_column_fails(self) -> None:
        schema = [
            {"column_name": "date", "column_type": "DATE"},
            {"column_name": "flight_number", "column_type": "DOUBLE"},
        ]

        with self.assertRaises(TableSchemaMismatchError):
            _validate_table_schema("flight_data", schema, CleanedFlightDuckDBTableCols)

    def test_wrong_order_fails(self) -> None:
        schema = [
            {"column_name": "flight_number", "column_type": "DOUBLE"},
            {"column_name": "date", "column_type": "DATE"},
            {"column_name": "origin", "column_type": "VARCHAR"},
            {"column_name": "origin_city_name", "column_type": "VARCHAR"},
            {"column_name": "dest", "column_type": "VARCHAR"},
            {"column_name": "dest_city_name", "column_type": "VARCHAR"},
            {"column_name": "pred_dep_time", "column_type": "BIGINT"},
            {"column_name": "pred_arr_time", "column_type": "BIGINT"},
            {"column_name": "pred_elapsed_time", "column_type": "DOUBLE"},
            {"column_name": "distance", "column_type": "DOUBLE"},
            {"column_name": "total_delay", "column_type": "DOUBLE"},
        ]

        with self.assertRaises(TableSchemaMismatchError):
            _validate_table_schema("flight_data", schema, CleanedFlightDuckDBTableCols)

    def test_wrong_type_fails(self) -> None:
        schema = [
            {"column_name": "date", "column_type": "VARCHAR"},
            {"column_name": "flight_number", "column_type": "DOUBLE"},
            {"column_name": "origin", "column_type": "VARCHAR"},
            {"column_name": "origin_city_name", "column_type": "VARCHAR"},
            {"column_name": "dest", "column_type": "VARCHAR"},
            {"column_name": "dest_city_name", "column_type": "VARCHAR"},
            {"column_name": "pred_dep_time", "column_type": "BIGINT"},
            {"column_name": "pred_arr_time", "column_type": "BIGINT"},
            {"column_name": "pred_elapsed_time", "column_type": "DOUBLE"},
            {"column_name": "distance", "column_type": "DOUBLE"},
            {"column_name": "total_delay", "column_type": "DOUBLE"},
        ]

        with self.assertRaises(TableSchemaMismatchError):
            _validate_table_schema("flight_data", schema, CleanedFlightDuckDBTableCols)


if __name__ == "__main__":
    unittest.main()
