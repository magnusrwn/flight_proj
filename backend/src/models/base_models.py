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
    date: date

class FuncResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    code: int | None = None
    message: str | None = None
    data: Any | None = None