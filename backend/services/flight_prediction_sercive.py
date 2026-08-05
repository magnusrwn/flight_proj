from typing import Any
import logging
from datetime import datetime
from pathlib import Path
import sys
import duckdb as ddb

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.utils import is_in_table
from src.api.aviation_api import fetch_scheduled_flight_info
from src.api.weather_api import fetch_weather_info
from src.models.base_models import (
    FuncResponse,
    PresentError,
    SendFlightRequest,
    RequestWithRetryResponse,
    MatchedAviationAPIDataResponse
)


logger = logging.getLogger(__name__)

# ==================== Helpers ====================
def match_flight_to_request(api_data:list[dict[str, Any]], req_flight:SendFlightRequest) -> FuncResponse:
    '''
    Itterates AviationStack API response to match the requested flight to the API response.
    '''
    for flight in api_data:
        api_dest_code = (flight.get("arrival") or {}).get("iataCode", "")
        api_iata_flight_code = (flight.get("flight") or {}).get("iataNumber", "")
        api_icao_flight_code = (flight.get("flight") or {}).get("icaoNumber", "")

        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Matching API response")
        if (
            api_dest_code.upper() == req_flight.destIataCode.upper()
            and req_flight.flightNumber.upper() in {
                api_iata_flight_code.upper(),
                api_icao_flight_code.upper(),
            }
        ):
            return FuncResponse(ok=True, code=200, data=flight)

    logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: No match found to API response")
    return FuncResponse(ok=False, code=404, message="Flight could not be matched to Aviation Stack response")

def build_flight_data(sch_dep_time:str, sch_arr_time:str, req_flight:SendFlightRequest) -> FuncResponse:
    '''
    Creates final flight datapoint from:
    - Duckdb (code, lat, long, name)
    - AviationStackAPI response
        - Calculating dates/ times based on times given here
    '''

    con = None
    try:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Open duckdb connection")
        con = ddb.connect(str(BACKEND_ROOT/"data/duck_database.duckdb"))
        air_match = con.execute(f"""
            SELECT
                dep.code,
                dep.name,
                dep.lat,
                dep.long,

                dest.code,
                dest.name,
                dest.lat,
                dest.long
            FROM airport_data AS dep
            JOIN airport_data AS dest ON TRUE
            WHERE dep.code = ? AND dest.code = ?
            LIMIT 1
        """
        ,[req_flight.depIataCode, req_flight.destIataCode]
        ).fetchone()

        if air_match is None:
            logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: No airport matches found")
            return FuncResponse(ok=False, code=404, message="No airport was matched to the airport_data dataset")
        (
            origin,
            origin_city_name,
            origin_lat,
            origin_long,
            dest,
            dest_city_name,
            dest_lat,
            dest_long           
        ) = air_match

        date = req_flight.date
        year = date.year
        month = date.month
        day_of_month = date.day
        day_of_week = date.isoweekday()

        sch_arr_time_obj = datetime.strptime(sch_arr_time, "%H:%M")
        sch_dep_time_obj = datetime.strptime(sch_dep_time, "%H:%M")
        elapsed_time:int = int((sch_arr_time_obj - sch_dep_time_obj).total_seconds() // 60)
        if elapsed_time < 0:
            elapsed_time += 24 * 60
        sch_dep_time_int:int=int(sch_dep_time_obj.strftime("%H%M"))
        sch_arr_time_int:int=int(sch_arr_time_obj.strftime("%H%M"))

        data = MatchedAviationAPIDataResponse(
            origin=origin,
            origin_city_name=origin_city_name,
            origin_lat=origin_lat,
            origin_long=origin_long,

            dest=dest,
            dest_city_name=dest_city_name,
            dest_lat=dest_lat,
            dest_long=dest_long,

            date=date,
            year=year,
            month=month,
            day_of_month=day_of_month,
            day_of_week=day_of_week,
            pred_dep_time=sch_dep_time_int,
            pred_arr_time=sch_arr_time_int,
            pred_elapsed_time=elapsed_time
        )

        return FuncResponse(
            ok=True,
            code=200,
            message="data ready for Open-MeteoAPI input",
            data=data.model_dump()
        )
    except ddb.ConnectionException as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Error establishing duckdb connection -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=500, message=str(e))
    except (ddb.CatalogException, ddb.BinderException) as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Error reading duckdb airport_data -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=400, message="Failed to read airport_data from duckdb", data=str(e))
    except ValueError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Error parsing scheduled times -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=400, message="Failed to parse scheduled flight times", data=str(e))
    finally:
        if con != None:
            logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Close duckdb connection")
            con.close()

# ==================== Service ====================
async def predict_flight__service(body:SendFlightRequest) -> FuncResponse:
    logger.info("%(asctime)s -- SERVICE START:send_flight__service")

    # Check is in table
    logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC START:is_in_table")
    is_in_table_resp:FuncResponse = is_in_table(
        table_name="weather_req_table",
        column="code",
        airprot_code=body.depIataCode
    )
    if not is_in_table_resp.ok:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:is_in_table -- DETAIL: %s", is_in_table_resp.message)
        code = is_in_table_resp.code or 500
        message = is_in_table_resp.message or "Failed checking airport against weather request table."
        return FuncResponse(
            ok=False,
            code=code,
            message=message,
            data=PresentError(
                code=code,
                description=message,
                error=str(is_in_table_resp.data) if is_in_table_resp.data is not None else None,
            ).model_dump(),
        )
    if is_in_table_resp.data is not True:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:is_in_table -- DETAIL: Airport %s not found", body.depIataCode)
        return FuncResponse(
            ok=False,
            code=404,
            message="Departure airport was not found in weather_req_table.",
            data=PresentError(
                code=404,
                description="Departure airport was not found in weather_req_table.",
                error=f"airport_code={body.depIataCode}",
            ).model_dump(),
        )


    # Aviation API
    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:fetch_scheduled_flight_info_resp")
    fetch_scheduled_flight_info_resp: RequestWithRetryResponse = await fetch_scheduled_flight_info(body)
    f_err = fetch_scheduled_flight_info_resp.error
    f_success = fetch_scheduled_flight_info_resp.success
    f_data = f_success.get("data") if f_success else None
    if f_err or not f_data:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:fetch_scheduled_flight_info_resp -- DETAIL: %s", f_err or "missing data")
        code = f_err.code if f_err else 502
        return FuncResponse(
            ok=False,
            code=code,
            message="Aviation API did not return scheduled flight data.",
            data=(
                f_err.model_dump()
                if f_err
                else PresentError(
                    code=code,
                    description="Aviation API did not return scheduled flight data.",
                    error=str(f_success) if f_success is not None else None,
                ).model_dump()
            ),
        )

    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:match_flight_to_request")
    flight_matched = match_flight_to_request(
        api_data=f_data,
        req_flight=body
    )
    if not flight_matched.ok:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:match_flight_to_request -- DETAIL: No flight matched to the AviationStack API response")
        code = flight_matched.code or 500
        message = flight_matched.message or "No flight matched to the AviationStack API response"
        return FuncResponse(
            ok=False,
            code=code,
            message=message,
            data=PresentError(
                code=code,
                description=message,
            ).model_dump(),
        )

    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:build_flight_data")
    matched_flight = flight_matched.data
    if not isinstance(matched_flight, dict):
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:match_flight_to_request -- DETAIL: Matched flight payload was invalid")
        return FuncResponse(
            ok=False,
            code=500,
            message="Matched Aviation API flight payload was invalid.",
            data=PresentError(
                code=500,
                description="Matched Aviation API flight payload was invalid.",
                error=str(matched_flight),
            ).model_dump(),
        )

    flight_sch_dep_time = matched_flight.get("departure", {}).get("scheduledTime", "")
    flight_sch_arr_time = matched_flight.get("arrival", {}).get("scheduledTime", "")
    if not flight_sch_dep_time or not flight_sch_arr_time:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_flight_data -- DETAIL: Missing scheduled times")
        return FuncResponse(
            ok=False,
            code=502,
            message="Matched Aviation API flight is missing scheduled departure or arrival time.",
            data=PresentError(
                code=502,
                description="Matched Aviation API flight is missing scheduled departure or arrival time.",
                error=str(matched_flight),
            ).model_dump(),
        )

    # Build data for Open-Meteo API
    built_data = build_flight_data(
        sch_dep_time=flight_sch_dep_time,
        sch_arr_time=flight_sch_arr_time,
        req_flight=body
    )
    if not built_data.ok:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_flight_data -- DETAIL: %s", built_data.message)
        code = built_data.code or 500
        message = built_data.message or "Failed to build flight data."
        return FuncResponse(
            ok=False,
            code=code,
            message=message,
            data=PresentError(
                code=code,
                description=message,
                error=str(built_data.data) if built_data.data is not None else None,
            ).model_dump(),
        )

    flight_data = built_data.data
    if not isinstance(flight_data, dict):
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_flight_data -- DETAIL: Built flight data payload was invalid")
        return FuncResponse(
            ok=False,
            code=500,
            message="Built flight data payload was invalid.",
            data=PresentError(
                code=500,
                description="Built flight data payload was invalid.",
                error=str(flight_data),
            ).model_dump(),
        )

    # Open-Meteo API
    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:fetch_origin_weather_info")
    origin_weather_resp: RequestWithRetryResponse = await fetch_weather_info(
        lat=flight_data["origin_lat"],
        lon=flight_data["origin_long"],
        date=body.date,
    )
    origin_weather_err = origin_weather_resp.error
    if origin_weather_err or not origin_weather_resp.success:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:fetch_origin_weather_info -- DETAIL: %s", origin_weather_err or "missing data")
        code = origin_weather_err.code if origin_weather_err else 502
        return FuncResponse(
            ok=False,
            code=code,
            message="Open-Meteo API did not return origin weather data.",
            data=(
                origin_weather_err.model_dump()
                if origin_weather_err
                else PresentError(
                    code=code,
                    description="Open-Meteo API did not return origin weather data.",
                    error=str(origin_weather_resp.success) if origin_weather_resp.success is not None else None,
                ).model_dump()
            ),
        )

    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:fetch_dest_weather_info")
    dest_weather_resp: RequestWithRetryResponse = await fetch_weather_info(
        lat=flight_data["dest_lat"],
        lon=flight_data["dest_long"],
        date=body.date,
    )
    dest_weather_err = dest_weather_resp.error
    if dest_weather_err or not dest_weather_resp.success:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:fetch_dest_weather_info -- DETAIL: %s", dest_weather_err or "missing data")
        code = dest_weather_err.code if dest_weather_err else 502
        return FuncResponse(
            ok=False,
            code=code,
            message="Open-Meteo API did not return destination weather data.",
            data=(
                dest_weather_err.model_dump()
                if dest_weather_err
                else PresentError(
                    code=code,
                    description="Open-Meteo API did not return destination weather data.",
                    error=str(dest_weather_resp.success) if dest_weather_resp.success is not None else None,
                ).model_dump()
            ),
        )

    # logger.info("%(asctime)s -- SERVICE END:send_flight__service -- DETAIL: Weather data ready")
    # return FuncResponse(
    #     ok=True,
    #     code=200,
    #     message="Weather data ready.",
    #     data={
    #         "flight_data": flight_data,
    #         "origin_weather_response": origin_weather_resp.model_dump(),
    #         "dest_weather_response": dest_weather_resp.model_dump(),
    #     },
    # )
