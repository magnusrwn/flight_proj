import duckdb as ddb
from pathlib import Path
from pydantic import BaseModel

class DataPipelineError(Exception):
    """Base exception for CSV-to-DuckDB pipeline failures."""

class CsvTableBuildError(DataPipelineError):
    """Raised when a CSV-backed table cannot be created or described."""

class WeatherRequestTableBuildError(DataPipelineError):
    """Raised when the weather request table cannot be created or described."""

class DataPipelineResponse(BaseModel):
    message: str | None = None
    data: dict | list[dict] | None = None

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
                fl_date AS date,
                op_carrier_fl_num AS flight_number,
                origin,
                origin_city_name,
                dest,
                dest_city_name ,
                crs_dep_time AS pred_dep_time,
                crs_arr_time AS pred_arr_time,
                crs_elapsed_time AS pred_elapsed_time,
                distance
            FROM read_csv_auto('{flight_data_path}')
        """)
    except Exception as e:
        raise CsvTableBuildError(
            f"Failed to create and clean flight data table '{table_name}' from '{flight_data_path}'."
        ) from e


    try:
        table_description = con.sql(f"DESCRIBE {table_name}").df()
    except Exception as e:
        raise CsvTableBuildError(
            f"Created flight data table '{table_name}', but failed to describe it."
        ) from e

    return DataPipelineResponse(
        message=f"Successfully created and cleaned flight data under table name: {table_name}",
        data=table_description.to_dict(orient='records')
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
            name,
            latitude_deg AS lat,
            longitude_deg AS long,
            iata_code AS code
        FROM read_csv_auto('{airport_data_path}')
        """)
    except Exception as e:
        raise CsvTableBuildError(
            f"Failed to create and clean airport data table '{table_name}' from '{airport_data_path}'."
        ) from e

    try:
        table_description = con.sql(f"DESCRIBE {table_name}").df()
    except Exception as e:
        raise CsvTableBuildError(
            f"Created airport data table '{table_name}', but failed to describe it."
        ) from e

    return DataPipelineResponse(
        message=f"Successfully created and cleaned airport data under table name: {table_name}",
        data=table_description.to_dict(orient='records')
    )

def create_weather_req_locations(
    con: ddb.DuckDBPyConnection,
    flight_table_name: str = "flight_data_sample",
    airport_table_name: str = "airport_data",
) -> DataPipelineResponse:
    try:
        con.sql(f"""
            CREATE OR REPLACE TABLE weather_req_table AS
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
            "Failed to create weather request table 'weather_req_table'."
        ) from e

    try:
        weather_req_table_description = con.sql("DESCRIBE weather_req_table").df()
    except Exception as e:
        raise WeatherRequestTableBuildError(
            "Created weather request table 'weather_req_table', but failed to describe it."
        ) from e

    return DataPipelineResponse(
        message="Successfully created 'weather_request_table'",
        data=weather_req_table_description.to_dict(orient='records')
    )
