from datetime import datetime
from pydantic import BaseModel


class CleanedFlightDuckDBTableCols(BaseModel):
    date: str | datetime
    flight_number: float 
    origin: str
    origin_city_name: str
    dest: str
    dest_city_name: str
    pred_dep_time: int
    pred_arr_time: int
    pred_elapsed_time: float
    distance: float

class CleanedAirportDuckDBTableCols(BaseModel):
    name: str
    lat:  float
    long: float
    code: str