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



# NOTE: Make model req model from this:
# id                                 bigint     flight_date                        date       year                               integer
# month                              integer    day_of_month                       integer    day_of_week                        integer
# flight_num                         double     origin                             varchar    origin_city_name                   varchar
# dest                               varchar    dest_city_name                     varchar    pred_dep_time                      bigint 
# pred_arr_time                      bigint     pred_elapsed_time                  double     fl_distance                        double 
# delay                              double     origin_weather_code                double     origin_temperature_2m_max          double 
# origin_temperature_2m_min          double     origin_apparent_temperature_max    double     origin_apparent_temperature_min    double 
# origin_precipitation_sum           double     origin_rain_sum                    double     origin_showers_sum                 double 
# origin_snowfall_sum                double     origin_cloud_cover_mean            double     origin_wind_speed_10m_max          double 
# origin_wind_gusts_10m_max          double     origin_wind_direction_10m_dominant double     origin_pressure_msl_mean           double 
# dest_weather_code                  double     dest_temperature_2m_max            double     dest_temperature_2m_min            double 
# dest_apparent_temperature_max      double     dest_apparent_temperature_min      double     dest_precipitation_sum             double 
# dest_rain_sum                      double     dest_showers_sum                   double     dest_snowfall_sum                  double 
# dest_cloud_cover_mean              double     dest_wind_speed_10m_max            double     dest_wind_gusts_10m_max            double 
# dest_wind_direction_10m_dominant   double     dest_pressure_msl_mean             double                          