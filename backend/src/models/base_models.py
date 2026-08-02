from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


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

class SendFlightNumberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iataCode: str = Field(max_length=3, min_length=3)
    date: datetime
