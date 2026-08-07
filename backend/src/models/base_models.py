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
    year: int
    month: int
    day_of_month: int
    day_of_week: int
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

    origin:str = Field(max_length=3, min_length=3)
    origin_city_name:str
    origin_lat:float
    origin_long:float

    dest:str = Field(max_length=3, min_length=3)
    dest_city_name:str
    dest_lat:float
    dest_long:float

    flight_date:date
    day_of_month:int
    day_of_week:int
    pred_dep_time:int
    pred_arr_time:int
    pred_elapsed_time:int
    year:int
    month:int

class SendWeatherAPIRequest(BaseModel):
    date: date
    lat: float
    long: float
