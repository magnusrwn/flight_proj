import duckdb as ddb
from pathlib import Path
from pydantic import BaseModel

class DataPipelineSuccessResponse(BaseModel):
    message: str | None = None
    data: dict | list[dict] | None = None

class DataPipelineErrorResponse(BaseModel):
    message: str | None = None
    error:  dict | list | None = None
    exceptions: list[str] | None = None

DATA_DIR = Path(__file__).resolve().parents[2]/"data"
FLIGHT_DATA = DATA_DIR/"csv/flight_data_2024.csv"
FLIGHT_DATA_SAMPLE = DATA_DIR/"csv/flight_data_2024_sample.csv"
AIRPORT_DATA = DATA_DIR/"csv/airport.csv"

# Kept cols for both datasets
FLIGHT_DATA_COLS_ALL = {'year', 'month', 'day_of_month', 'day_of_week', 'fl_date',
       'op_unique_carrier', 'op_carrier_fl_num', 'origin', 'origin_city_name',
       'origin_state_nm', 'dest', 'dest_city_name', 'dest_state_nm',
       'crs_dep_time', 'dep_time', 'dep_delay', 'taxi_out', 'wheels_off',
       'wheels_on', 'taxi_in', 'crs_arr_time', 'arr_time', 'arr_delay',
       'cancelled', 'cancellation_code', 'diverted', 'crs_elapsed_time',
       'actual_elapsed_time', 'air_time', 'distance', 'carrier_delay',
       'weather_delay', 'nas_delay', 'security_delay', 'late_aircraft_delay'}

FLIGHT_DATA_COLS_TO_DROP = ['year', 'month', 'day_of_month', 'day_of_week','op_unique_carrier',
       'origin_state_nm', 'dest_state_nm', 'dep_time', 'dep_delay', 'taxi_out', 'wheels_off',
       'wheels_on', 'arr_time', 'arr_delay', 'cancelled', 'cancellation_code', 'diverted',
       'actual_elapsed_time', 'air_time', 'carrier_delay',
       'weather_delay', 'nas_delay', 'security_delay', 'late_aircraft_delay']



AIRPORT_COLS_ALL = {'id', 'ident', 'type', 'name', 'latitude_deg', 'longitude_deg',
       'elevation_ft', 'continent', 'iso_country', 'iso_region',
       'municipality', 'scheduled_service', 'icao_code', 'iata_code',
       'gps_code', 'local_code', 'home_link', 'wikipedia_link', 'keywords'}

AIRPORT_COLS_TO_DROP = ['id', 'ident', 'type', 'elevation_ft', 'continent',
        'iso_country', 'iso_region', 'municipality', 'scheduled_service', 'icao_code',
        'gps_code', 'local_code','home_link', 'wikipedia_link', 'keywords']

AIRPORT_DATA_NEW_NAMES = {'latitude_deg':'lat', 'longitude_deg':'long', 'iata_code':'code'}

def table_exists(con:ddb.DuckDBPyConnection, table_name:str) -> tuple[bool, list[str] | None]:
    """
    Checks...
    - Table exists within the specified db
    - Table has >= 1 datapoint(s)
    """
    exceptions: list[str] = []
    try:
        row = con.sql(f"SELECT 1 FROM {table_name} LIMIT 1").fetchone()
        return row is not None, None
    except Exception as exc:
        exceptions.append(str(exc))
        return False, exceptions

def create_duckdb_table(con:ddb.DuckDBPyConnection, table_name:str, csv_path:Path | str) -> None:
    con.sql(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM read_csv_auto('{csv_path}')
    """)

def create_and_clean_flights_table(con:ddb.DuckDBPyConnection, table_name:str, flight_data_path:Path|str) -> DataPipelineErrorResponse | DataPipelineSuccessResponse:
    """
    This function cleans and formats the flight_data with the following process:
    - Creates the flight_data table in the duckdb
    - Drops cols in 'FLIGHT_DATA_COLS_TO_DROP'
    
    The csv must fit the shape of/be the flights dataset specified in project docs
    """
    # create table
    create_duckdb_table(con, table_name, flight_data_path)

    # ensure the table exists
    table_ok, exceptions = table_exists(con, table_name)
    if not table_ok:
        return DataPipelineErrorResponse(
            message="Table does not exists and/ or has no data",
            error=None,
            exceptions=exceptions
        )

    # Check it the shape is the same
    desc = con.sql(f"DESCRIBE {table_name}").df()
    cols = set(desc.column_name)
    if not cols == FLIGHT_DATA_COLS_ALL:
        return DataPipelineErrorResponse(
            message="Col miss-match see col errs in error:'unexpected_cols', and error:'missing_cols'",
            error={
                "unexpected_cols":cols - FLIGHT_DATA_COLS_ALL,
                "missing_cols": FLIGHT_DATA_COLS_ALL - cols
            } 
        )

    # Drop cols -- all cols are the same, so can't (really) fail
    for to_drop in FLIGHT_DATA_COLS_TO_DROP:
        con.sql(f"ALTER TABLE {table_name} DROP COLUMN {to_drop}")

    table_description = con.sql(f"DESCRIBE {table_name}").df()

    return DataPipelineSuccessResponse(
        message=f"Successfully created and cleaned flight_data udner table name: {table_name}",
        data=table_description.to_dict(orient="records")
    )


def create_and_clean_airport_table(con:ddb.DuckDBPyConnection, table_name:str, airport_data_path:Path|str) -> DataPipelineErrorResponse | DataPipelineSuccessResponse:
    """
    This function cleans and formats the airprot_data with the following process:
    - Creates the airprot_data table in specified duckdb
    - Drops cols in 'AIRPORT_COLS_TO_DROP'
    
    The csv data must fit the shape of/ be the airprots dataset specified in project docs
    """
    create_duckdb_table(con, table_name, airport_data_path)

    # ensure the table exists
    table_ok, exceptions = table_exists(con, table_name)
    if not table_ok:
        return DataPipelineErrorResponse(
            message="Table does not exists and/ or has no data",
            error=None,
            exceptions=exceptions
        )

    # Check it the shape is the same
    desc = con.sql(f"DESCRIBE {table_name}").df()
    cols = set(desc.column_name)
    if not cols == AIRPORT_COLS_ALL:
        return DataPipelineErrorResponse(
            message="Col miss-match see col errs in: error:'unexpected_cols', and error:'missing_cols'",
            error={
                "unexpected_cols":cols - AIRPORT_COLS_ALL,
                "missing_cols": AIRPORT_COLS_ALL - cols
            } 
        )

    # Drop cols -- all cols are the same, so can't (really) fail
    for to_drop in AIRPORT_COLS_TO_DROP:
        con.sql(f"ALTER TABLE {table_name} DROP COLUMN {to_drop}")

    # rename cols:
    for cur_col_name in AIRPORT_DATA_NEW_NAMES:
        con.sql(f"ALTER TABLE {table_name} RENAME COLUMN {cur_col_name} TO {AIRPORT_DATA_NEW_NAMES[cur_col_name]}")

    table_description = con.sql(f"DESCRIBE {table_name}").df()

    return DataPipelineSuccessResponse(
        message=f"Successfully created and cleaned airport_data udner table name: {table_name}",
        data=table_description.to_dict(orient="records")
    )
