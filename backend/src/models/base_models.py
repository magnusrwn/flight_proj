from datetime import datetime
from pydantic import BaseModel


class CleanedFlightDuckDBTable(BaseModel):
    fl_date: str | datetime
    op_carrier_fl_num: float 
    origin: str
    origin_city_name: str
    dest: str
    dest_city_name: str
    crs_dep_time: int
    crs_arr_time: int
    crs_elapsed_time: float
    distance: float

class CleanedAirportDuckDBTable(BaseModel):
    name: str
    lat:  float
    long: float
    code: str