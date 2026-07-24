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

def create_and_clean_flights_table(
    con:ddb.DuckDBPyConnection,
    table_name:str,
    flight_data_path:Path|str
) -> DataPipelineErrorResponse | DataPipelineSuccessResponse:
    """
    *The csv MUST fit the shape of/be the flights dataset specified in project docs, and in the pipelile process*
    
    This function cleans and formats the flight_data with the following process:
    - Creates the flight_data table in the duckdb
    - Returns the new structure of the flights data in response
    
    """
    exceptions: list[str]= []
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
        exceptions.append(str(e))

    if exceptions:
        return DataPipelineErrorResponse(
            message=f"Failed to create & clean flight data table for: {table_name}. See exception.",
            exceptions=exceptions
        )
    table_description = con.sql(f"DESCRIBE {table_name}").df()
    return DataPipelineSuccessResponse(
        message=f"Successfully created and cleaned flight data under table name: {table_name}",
        data=table_description.to_dict(orient='records')
    )

def create_and_clean_airport_table(
    con:ddb.DuckDBPyConnection,
    table_name:str,
    airport_data_path:Path|str
) -> DataPipelineErrorResponse | DataPipelineSuccessResponse:
    """
    *The csv data MUST fit the shape of/ be the airprots dataset specified in project docs and in the pipeline process*
    
    This function cleans and formats the airprot_data with the following process:
    - Creates the airprot_data table in specified duckdb
    - Returns the new structure of the airports data in response

    """

    exceptions: list[str] = []
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
        exceptions.append(str(e))

    if exceptions:
        return DataPipelineErrorResponse(
            message=f"Failed to create & clean airport data table for: {table_name}. See exception.",
            exceptions=exceptions
        )

    table_description = con.sql(f"DESCRIBE {table_name}").df()
    return DataPipelineSuccessResponse(
        message=f"Successfully created and cleaned airport data under table name: {table_name}",
        data=table_description.to_dict(orient='records')
    )

def create_weather_req_locations(con:ddb.DuckDBPyConnection):
    
    pass
