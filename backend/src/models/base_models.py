from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Any

class PresentError(BaseModel):
    code: int
    description: str
    error: str | None = None

class RequestWithRetryResponse(BaseModel):
    success: dict[str, Any] | None = None
    error: PresentError | None = None

class CleanedFlightDuckDBTableCols(BaseModel):
    date: date
    flight_number: float
    origin: str
    origin_city_name: str
    dest: str
    dest_city_name: str
    pred_dep_time: int
    pred_arr_time: int
    pred_elapsed_time: float
    distance: float
    total_delay: float

class CleanedAirportDuckDBTableCols(BaseModel):
    name: str
    lat: float
    long: float
    code: str

class WeatherRequestDuckDBTableCols(BaseModel):
    date: date
    code: str
    name: str
    lat: float
    long: float
    status: str
    attempt_count: int
    last_error: str | None
    updated_at: datetime

class SendFlightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depIataCode: str = Field(max_length=3, min_length=3)
    destIataCode: str = Field(max_length=3, min_length=3)
    date: date
    flightNumber: str

class FuncResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    code: int | None = None
    message: str | None = None
    data: Any | None = None

class MatchedAviationAPIDataResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    error: dict[str:Any] | None = None
# NOTE: I have in API respp/ duckdb:
    # date (sp i can get date, year, month, day of month, day_of_week)
    # "weekday": "6",
    # "departure": {
    #   "iataCode": "lys",
    #   "scheduledTime": "07:00"
    # },
    # "arrival": {
    #   "iataCode": "lgw",
    #   "scheduledTime": "07:40"
    # },
    # "aircraft": {
    #   "modelCode": "a320",
    #   "modelText": "airbus a320-214"
    # },
    # "airline": {
    #   "name": "easyjet",
    #   "iataCode": "u2",
    #   "icaoCode": "ezy"
    # },
    # "flight": {
    #   "number": "8430",
    #   "iataNumber": "u28430",
    #   "icaoNumber": "ezy8430"
    # }
    # NOTE: Match origin/dest city names with airport duckdb
    # NOTE: calculate the elapsed time
    # 
│ date              date    │
│ year              integer │
│ month             integer │
│ day_of_month      integer │
│ day_of_week       integer │
│ flight_number     double  │
│ origin            varchar │
│ origin_city_name  varchar │
│ dest              varchar │
│ dest_city_name    varchar │
│ pred_dep_time     bigint  │
│ pred_arr_time     bigint  │
│ pred_elapsed_time double  │
│ distance  