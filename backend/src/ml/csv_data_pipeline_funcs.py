import duckdb as ddb
from datetime import date, datetime
from pathlib import Path
from types import UnionType
from typing import Any, get_args, get_origin
from pydantic import BaseModel
import sys

BACKEND_SRC_PATH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_SRC_PATH))
from models.base_models import (
    CleanedAirportDuckDBTableCols,
    CleanedFlightDuckDBTableCols,
    WeatherRequestDuckDBTableCols,
)

class DataPipelineError(Exception):
    """Base exception for CSV-to-DuckDB pipeline failures."""

class CsvTableBuildError(DataPipelineError):
    """Raised when a CSV-backed table cannot be created or described."""

class WeatherRequestTableBuildError(DataPipelineError):
    """Raised when the weather request table cannot be created or described."""

class TableSchemaMismatchError(DataPipelineError):
    """Raised when a built DuckDB table does not match its model contract."""

class TableInvariantError(DataPipelineError):
    """Raised when a built DuckDB table violates cheap relational invariants."""

class DataPipelineResponse(BaseModel):
    message: str | None = None
    data: dict | list[dict] | None = None


_MODEL_TYPE_TO_DUCKDB: dict[type, set[str]] = {
    str: {"VARCHAR"},
    int: {"BIGINT", "INTEGER", "SMALLINT", "TINYINT", "UBIGINT", "UINTEGER", "USMALLINT"},
    float: {"DOUBLE", "FLOAT", "REAL", "DECIMAL"},
    date: {"DATE"},
    datetime: {"TIMESTAMP", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP_TZ"},
}


def _normalise_duckdb_type(type_name: str) -> str:
    normalised = type_name.strip().upper()
    if "(" in normalised:
        normalised = normalised.split("(", 1)[0].strip()
    return normalised


def _expected_schema_from_model(model: type[BaseModel]) -> list[tuple[str, set[str]]]:
    expected_schema: list[tuple[str, set[str]]] = []
    for field_name, field_info in model.model_fields.items():
        annotation = field_info.annotation
        origin = get_origin(annotation)
        if origin in (UnionType,):
            annotation_types = get_args(annotation)
        elif origin is not None:
            annotation_types = get_args(annotation)
        else:
            annotation_types = (annotation,)

        allowed_types: set[str] = set()
        for annotation_type in annotation_types:
            if annotation_type is type(None):
                continue
            try:
                allowed_types.update(_MODEL_TYPE_TO_DUCKDB[annotation_type])
            except KeyError as exc:
                raise TableSchemaMismatchError(
                    f"Unsupported model annotation '{annotation_type}' on field '{field_name}'."
                ) from exc

        if not allowed_types:
            raise TableSchemaMismatchError(
                f"Field '{field_name}' on model '{model.__name__}' does not map to a DuckDB type."
            )
        expected_schema.append((field_name, allowed_types))
    return expected_schema


def _validate_table_schema(
    table_name: str,
    table_description: list[dict[str, Any]],
    model: type[BaseModel],
) -> None:
    expected_schema = _expected_schema_from_model(model)
    actual_schema = [
        (column["column_name"], _normalise_duckdb_type(column["column_type"]))
        for column in table_description
    ]

    if len(expected_schema) != len(actual_schema):
        raise TableSchemaMismatchError(
            f"Table '{table_name}' has {len(actual_schema)} columns, expected {len(expected_schema)} "
            f"from model '{model.__name__}'. Actual schema: {actual_schema}"
        )
    for (expected_name, expected_types), (actual_name, actual_type) in zip(expected_schema, actual_schema, strict=True):
        if actual_name != expected_name:
            raise TableSchemaMismatchError(
                f"Table '{table_name}' column order/name mismatch. Expected '{expected_name}', "
                f"found '{actual_name}'."
            )
        if actual_type not in expected_types:
            raise TableSchemaMismatchError(
                f"Table '{table_name}' column '{actual_name}' has type '{actual_type}', "
                f"expected one of {sorted(expected_types)} from model '{model.__name__}'."
            )


def _ensure_table_not_empty(con: ddb.DuckDBPyConnection, table_name: str) -> None:
    row_count = con.sql(f"SELECT COUNT(*) AS row_count FROM {table_name}").fetchone()[0]
    if row_count == 0:
        raise TableInvariantError(f"Table '{table_name}' is empty.")


def _ensure_non_null_key_columns(
    con: ddb.DuckDBPyConnection,
    table_name: str,
    column_names: list[str],
) -> None:
    where_clause = " OR ".join(f"{column_name} IS NULL" for column_name in column_names)
    null_count = con.sql(
        f"SELECT COUNT(*) AS null_count FROM {table_name} WHERE {where_clause}"
    ).fetchone()[0]
    if null_count > 0:
        raise TableInvariantError(
            f"Table '{table_name}' has {null_count} rows with nulls in required columns {column_names}."
        )

def create_and_clean_flights_table(
    con:ddb.DuckDBPyConnection,
    table_name:str,
    flight_data_path:Path|str
) -> DataPipelineResponse:
    """
    *The csv MUST fit the shape of/be the flights dataset specified in project docs, and in the pipelile process*
    
    This function cleans and formats the flight_data with the following process:
    - Creates the flight_data table in the duckdb
    - Returns the new structure of the flights data in response
    
    """
    try:
        con.sql(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT
                CAST(fl_date AS DATE) AS date,
                CAST(op_carrier_fl_num AS DOUBLE) AS flight_number,
                CAST(origin AS VARCHAR) AS origin,
                CAST(origin_city_name AS VARCHAR) AS origin_city_name,
                CAST(dest AS VARCHAR) AS dest,
                CAST(dest_city_name AS VARCHAR) AS dest_city_name,
                CAST(crs_dep_time AS BIGINT) AS pred_dep_time,
                CAST(crs_arr_time AS BIGINT) AS pred_arr_time,
                CAST(crs_elapsed_time AS DOUBLE) AS pred_elapsed_time,
                CAST(distance AS DOUBLE) AS distance
            FROM read_csv_auto('{flight_data_path}')
        """)
    except Exception as e:
        raise CsvTableBuildError(
            f"Failed to create and clean flight data table '{table_name}' from '{flight_data_path}'."
        ) from e


    try:
        table_description = con.sql(f"DESCRIBE {table_name}").fetchdf()
    except Exception as e:
        raise CsvTableBuildError(
            f"Created flight data table '{table_name}', but failed to describe it."
        ) from e

    table_description_records = table_description.to_dict(orient='records')

    try:
        _validate_table_schema(table_name, table_description_records, CleanedFlightDuckDBTableCols)
        _ensure_table_not_empty(con, table_name)
        _ensure_non_null_key_columns(con, table_name, ["date", "flight_number", "origin", "dest"])
    except DataPipelineError as e:
        raise CsvTableBuildError(
            f"Cleaned flight data table '{table_name}' failed validation."
        ) from e

    return DataPipelineResponse(
        message=f"Successfully created and cleaned flight data under table name: {table_name}",
        data=table_description_records
    )

def create_and_clean_airport_table(
    con:ddb.DuckDBPyConnection,
    table_name:str,
    airport_data_path:Path|str
) -> DataPipelineResponse:
    """
    *The csv data MUST fit the shape of/ be the airprots dataset specified in project docs and in the pipeline process*
    
    This function cleans and formats the airprot_data with the following process:
    - Creates the airprot_data table in specified duckdb
    - Returns the new structure of the airports data in response

    """
    try:
        con.sql(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT
            CAST(name AS VARCHAR) AS name,
            CAST(latitude_deg AS DOUBLE) AS lat,
            CAST(longitude_deg AS DOUBLE) AS long,
            CAST(iata_code AS VARCHAR) AS code
        FROM read_csv_auto('{airport_data_path}')
        WHERE iata_code IS NOT NULL
        """)
    except Exception as e:
        raise CsvTableBuildError(
            f"Failed to create and clean airport data table '{table_name}' from '{airport_data_path}'."
        ) from e

    try:
        table_description = con.sql(f"DESCRIBE {table_name}").fetchdf()
    except Exception as e:
        raise CsvTableBuildError(
            f"Created airport data table '{table_name}', but failed to describe it."
        ) from e

    table_description_records = table_description.to_dict(orient='records')

    try:
        _validate_table_schema(table_name, table_description_records, CleanedAirportDuckDBTableCols)
        _ensure_table_not_empty(con, table_name)
        _ensure_non_null_key_columns(con, table_name, ["name", "lat", "long", "code"])
    except DataPipelineError as e:
        raise CsvTableBuildError(
            f"Cleaned airport data table '{table_name}' failed validation."
        ) from e

    return DataPipelineResponse(
        message=f"Successfully created and cleaned airport data under table name: {table_name}",
        data=table_description_records
    )

def create_weather_req_locations(
    con: ddb.DuckDBPyConnection,
    flight_table_name: str = "flight_data_sample",
    airport_table_name: str = "airport_data",
) -> DataPipelineResponse:
    weather_table_name = "weather_req_table"
    try:
        con.sql(f"""
            CREATE OR REPLACE TABLE {weather_table_name} AS
            WITH airport_date AS (
                SELECT date, origin AS code
                FROM {flight_table_name}

                UNION

                SELECT date, dest AS code
                FROM {flight_table_name}
            )
            SELECT
                ad.date,
                ad.code,
                a.name,
                a.lat,
                a.long
            FROM airport_date AS ad
            JOIN {airport_table_name} a
                ON ad.code = a.code
        """)
    except Exception as e:
        raise WeatherRequestTableBuildError(
            f"Failed to create weather request table '{weather_table_name}'."
        ) from e

    try:
        weather_req_table_description = con.sql(f"DESCRIBE {weather_table_name}").fetchdf()
    except Exception as e:
        raise WeatherRequestTableBuildError(
            f"Created weather request table '{weather_table_name}', but failed to describe it."
        ) from e

    weather_req_table_description_records = weather_req_table_description.to_dict(orient='records')

    try:
        _validate_table_schema(
            weather_table_name,
            weather_req_table_description_records,
            WeatherRequestDuckDBTableCols,
        )
        _ensure_table_not_empty(con, weather_table_name)
        _ensure_non_null_key_columns(con, weather_table_name, ["date", "code", "name", "lat", "long"])
    except DataPipelineError as e:
        raise WeatherRequestTableBuildError(
            f"Weather request table '{weather_table_name}' failed validation."
        ) from e

    return DataPipelineResponse(
        message=f"Successfully created '{weather_table_name}'",
        data=weather_req_table_description_records
    )
