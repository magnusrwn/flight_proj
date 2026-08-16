from datetime import date, datetime, time
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

class FlightPredRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    scheduledDepartureTime: time
    depIataCode: str = Field(max_length=3, min_length=3)
    destIataCode: str = Field(max_length=3, min_length=3)

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

class FlightDistanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin_lat: float = Field(ge=-90, le=90)
    origin_long: float = Field(ge=-180, le=180)
    dest_lat: float = Field(ge=-90, le=90)
    dest_long: float = Field(ge=-180, le=180)

class FlightDistanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fl_distance: int = Field(ge=0)

class FlightPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_significant_delay: bool
    significant_delay_probability: float | None = Field(default=None, ge=0, le=1)

    coordinates: FlightDistanceRequest
    distance: FlightDistanceResponse
    aviationApiData: MatchedAviationAPIDataResponse

class MLModelCategoricalInput(BaseModel):
    flight_date: date
    origin: str = Field(max_length=3, min_length=3)
    dest: str = Field(max_length=3, min_length=3)

class MLModelNumericInput(BaseModel):
    year: int
    month: int
    day_of_month: int
    day_of_week: int
    pred_dep_time: int
    pred_arr_time: int
    pred_elapsed_time: int
    fl_distance: int
    origin_weather_code: float
    origin_apparent_temperature_max: float
    origin_temperature_2m_max: float
    origin_temperature_2m_min: float
    origin_apparent_temperature_min: float
    origin_precipitation_sum: float
    origin_rain_sum: float
    origin_showers_sum: float
    origin_snowfall_sum: float
    origin_cloud_cover_mean: float
    origin_wind_speed_10m_max: float
    origin_wind_gusts_10m_max: float
    origin_wind_direction_10m_dominant: float
    origin_pressure_msl_mean: float
    dest_weather_code: float
    dest_temperature_2m_max: float
    dest_temperature_2m_min: float
    dest_apparent_temperature_max: float
    dest_apparent_temperature_min: float
    dest_precipitation_sum: float
    dest_rain_sum: float
    dest_showers_sum: float
    dest_snowfall_sum: float
    dest_cloud_cover_mean: float
    dest_wind_speed_10m_max: float
    dest_wind_gusts_10m_max: float
    dest_wind_direction_10m_dominant: float
    dest_pressure_msl_mean: float

class MLModelInput(BaseModel):
    numerical_input: MLModelNumericInput
    categorical_input: MLModelCategoricalInput
