from typing import Any
import logging
from datetime import datetime
from pathlib import Path
import sys
import duckdb as ddb
import joblib
import pandas as pd
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.utils import calculate_distance_miles, is_in_table, get_nested_str
from src.api.aviation_api import fetch_scheduled_flight_info
from src.api.weather_api import WEATHER_DAILY_FIELDS, fetch_weather_info
from src.models.base_models import (
    FlightDistanceRequest,
    FlightDistanceResponse,
    FlightPredictionResponse,
    FuncResponse,
    MLModelCatagoricalInput,
    MLModelInput,
    MLModelNumericInput,
    PresentError,
    FlightPredRequest,
    RequestWithRetryResponse,
    MatchedAviationAPIDataResponse
)


logger = logging.getLogger(__name__)

MODEL_PATH = BACKEND_ROOT / "src/ml/model/model.joblib"
MODEL_FEATURES = [
    "year",
    "month",
    "day_of_month",
    "day_of_week",
    "pred_dep_time",
    "pred_arr_time",
    "pred_elapsed_time",
    "fl_distance",
    "origin_weather_code",
    "origin_temperature_2m_max",
    "origin_temperature_2m_min",
    "origin_apparent_temperature_max",
    "origin_apparent_temperature_min",
    "origin_precipitation_sum",
    "origin_rain_sum",
    "origin_showers_sum",
    "origin_snowfall_sum",
    "origin_cloud_cover_mean",
    "origin_wind_speed_10m_max",
    "origin_wind_gusts_10m_max",
    "origin_wind_direction_10m_dominant",
    "origin_pressure_msl_mean",
    "dest_weather_code",
    "dest_temperature_2m_max",
    "dest_temperature_2m_min",
    "dest_apparent_temperature_max",
    "dest_apparent_temperature_min",
    "dest_precipitation_sum",
    "dest_rain_sum",
    "dest_showers_sum",
    "dest_snowfall_sum",
    "dest_cloud_cover_mean",
    "dest_wind_speed_10m_max",
    "dest_wind_gusts_10m_max",
    "dest_wind_direction_10m_dominant",
    "dest_pressure_msl_mean",
    "flight_date",
    "origin",
    "dest",
]

# ==================== Helpers ====================
def match_flight_to_request(api_data:list[dict[str, Any]], req_flight:FlightPredRequest) -> FuncResponse:
    '''
    Itterates AviationStack API response to match the requested flight to the API response.
    '''
    for flight in api_data:
        if not isinstance(flight, dict):
            logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:match_flight_to_request -- DETAIL: Skipping invalid flight payload")
            continue

        api_dest_code = get_nested_str(flight, "arrival", "iataCode")
        api_iata_flight_code = get_nested_str(flight, "flight", "iataNumber")
        api_icao_flight_code = get_nested_str(flight, "flight", "icaoNumber")

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

def build_flight_data(sch_dep_time:str, sch_arr_time:str, req_flight:FlightPredRequest) -> FuncResponse:
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

            flight_date=date,
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

def build_flight_distance(flight_data: dict[str, Any]) -> FuncResponse:
    try:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:build_flight_distance -- DETAIL: Calculating flight distance")
        distance_request = FlightDistanceRequest(
            origin_lat=flight_data["origin_lat"],
            origin_long=flight_data["origin_long"],
            dest_lat=flight_data["dest_lat"],
            dest_long=flight_data["dest_long"],
        )
        fl_distance = calculate_distance_miles(**distance_request.model_dump())
        distance_response = FlightDistanceResponse(fl_distance=fl_distance)
        return FuncResponse(
            ok=True,
            code=200,
            message="Flight distance calculated.",
            data=distance_response.model_dump(),
        )
    except KeyError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:build_flight_distance -- DETAIL: Missing coordinate -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=500, message="Built flight data is missing distance coordinates.", data=str(e))
    except ValidationError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:build_flight_distance -- DETAIL: Coordinate validation failed -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=400, message="Flight distance data failed validation.", data=str(e))
    except ValueError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:build_flight_distance -- DETAIL: Distance calculation failed -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=400, message="Flight distance could not be calculated.", data=str(e))

def extract_daily_weather_features(weather_data: dict[str, Any], prefix: str) -> FuncResponse:
    try:
        daily = weather_data.get("daily")
        if not isinstance(daily, dict):
            return FuncResponse(ok=False, code=502, message=f"{prefix} weather daily payload was invalid.", data=str(weather_data))

        features: dict[str, float] = {}
        for field in WEATHER_DAILY_FIELDS:
            values = daily.get(field)
            if not isinstance(values, list) or not values:
                return FuncResponse(ok=False, code=502, message=f"{prefix} weather field '{field}' was missing or invalid.", data=str(daily))

            value = values[0]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return FuncResponse(ok=False, code=502, message=f"{prefix} weather field '{field}' value was invalid.", data=str(values))

            features[f"{prefix}_{field}"] = float(value)

        return FuncResponse(ok=True, code=200, message=f"{prefix} weather features extracted.", data=features)
    except ValueError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:extract_daily_weather_features -- DETAIL: Weather extraction failed -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=502, message=f"{prefix} weather data could not be extracted.", data=str(e))

def build_ml_model_input(
    flight_data: dict[str, Any],
    origin_weather_data: dict[str, Any],
    dest_weather_data: dict[str, Any],
) -> FuncResponse:
    try:
        origin_weather_resp = extract_daily_weather_features(origin_weather_data, "origin")
        if not origin_weather_resp.ok:
            return origin_weather_resp
        dest_weather_resp = extract_daily_weather_features(dest_weather_data, "dest")
        if not dest_weather_resp.ok:
            return dest_weather_resp

        if not isinstance(origin_weather_resp.data, dict) or not isinstance(dest_weather_resp.data, dict):
            return FuncResponse(ok=False, code=500, message="Weather feature payload was invalid.", data={
                "origin": origin_weather_resp.data,
                "dest": dest_weather_resp.data,
            })

        numerical_input = MLModelNumericInput(
            year=flight_data["year"],
            month=flight_data["month"],
            day_of_month=flight_data["day_of_month"],
            day_of_week=flight_data["day_of_week"],
            pred_dep_time=flight_data["pred_dep_time"],
            pred_arr_time=flight_data["pred_arr_time"],
            pred_elapsed_time=flight_data["pred_elapsed_time"],
            fl_distance=flight_data["fl_distance"],
            **origin_weather_resp.data,
            **dest_weather_resp.data,
        )
        catagorical_input = MLModelCatagoricalInput(
            flight_date=flight_data["flight_date"],
            origin=flight_data["origin"],
            dest=flight_data["dest"],
        )
        model_input = MLModelInput(
            numerical_input=numerical_input,
            catagorical_input=catagorical_input,
        )
        return FuncResponse(
            ok=True,
            code=200,
            message="ML model input validated.",
            data=model_input.model_dump(),
        )
    except KeyError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:build_ml_model_input -- DETAIL: Missing model input field -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=500, message="ML model input is missing required flight data.", data=str(e))
    except ValidationError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:build_ml_model_input -- DETAIL: Model input validation failed -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=400, message="ML model input failed validation.", data=str(e))

def predict_delay_from_model(model_input: dict[str, Any]) -> FuncResponse:
    try:
        numerical_input = model_input["numerical_input"]
        catagorical_input = model_input["catagorical_input"]
        if not isinstance(numerical_input, dict) or not isinstance(catagorical_input, dict):
            return FuncResponse(ok=False, code=500, message="ML model input payload was invalid.", data=str(model_input))

        model_row = {**numerical_input, **catagorical_input}
        model_df = pd.DataFrame([model_row], columns=MODEL_FEATURES)
        model_df["pred_elapsed_time"] = model_df["pred_elapsed_time"].astype(float)
        model_df["fl_distance"] = model_df["fl_distance"].astype(float)
        model_df["flight_date"] = pd.to_datetime(model_df["flight_date"])

        model = joblib.load(MODEL_PATH)
        prediction = int(model.predict(model_df)[0])
        probability = None
        if hasattr(model, "predict_proba"):
            probability = float(model.predict_proba(model_df)[0][1])

        return FuncResponse(
            ok=True,
            code=200,
            message="Flight delay prediction complete.",
            data={
                "is_significant_delay": bool(prediction),
                "significant_delay_probability": probability,
            },
        )
    except KeyError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:predict_delay_from_model -- DETAIL: Missing model input field -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=500, message="ML model input is missing required fields.", data=str(e))
    except FileNotFoundError as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:predict_delay_from_model -- DETAIL: Model file missing -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=500, message="ML model file was not found.", data=str(e))
    except Exception as e:
        logger.info("%(asctime)s -- SERVICE:send_flight__service - FUNC:predict_delay_from_model -- DETAIL: Model prediction failed -- MESSAGE: %s", str(e))
        return FuncResponse(ok=False, code=500, message="ML model prediction failed.", data=str(e))

# ==================== Service ====================
async def predict_flight__service(body:FlightPredRequest) -> FuncResponse:
    logger.info("%(asctime)s -- SERVICE START:send_flight__service")


    # === Check the aiport input is good ===
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


    # === Sending flight-data API request
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
    if not isinstance(f_data, list):
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:fetch_scheduled_flight_info_resp -- DETAIL: Aviation API data payload was invalid")
        return FuncResponse(
            ok=False,
            code=502,
            message="Aviation API scheduled flight data payload was invalid.",
            data=PresentError(
                code=502,
                description="Aviation API scheduled flight data payload was invalid.",
                error=str(f_data),
            ).model_dump(),
        )


    # === Matching flight-data resp to request sent ===
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


    # === Building flight-data from API resp ===
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

    flight_sch_dep_time = get_nested_str(matched_flight, "departure", "scheduledTime")
    flight_sch_arr_time = get_nested_str(matched_flight, "arrival", "scheduledTime")
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


    # === Build data for Open-Meteo API ===
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


    # === Calc flight distance ===
    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:build_flight_distance")
    distance_resp = build_flight_distance(flight_data)
    if not distance_resp.ok:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_flight_distance -- DETAIL: %s", distance_resp.message)
        code = distance_resp.code or 500
        message = distance_resp.message or "Failed to calculate flight distance."
        return FuncResponse(
            ok=False,
            code=code,
            message=message,
            data=PresentError(
                code=code,
                description=message,
                error=str(distance_resp.data) if distance_resp.data is not None else None,
            ).model_dump(),
        )

    if not isinstance(distance_resp.data, dict) or "fl_distance" not in distance_resp.data:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_flight_distance -- DETAIL: Distance payload was invalid")
        return FuncResponse(
            ok=False,
            code=500,
            message="Flight distance payload was invalid.",
            data=PresentError(
                code=500,
                description="Flight distance payload was invalid.",
                error=str(distance_resp.data),
            ).model_dump(),
        )
    fl_distance = distance_resp.data["fl_distance"]
    if not isinstance(fl_distance, int) or isinstance(fl_distance, bool):
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_flight_distance -- DETAIL: Distance value was invalid")
        return FuncResponse(
            ok=False,
            code=500,
            message="Flight distance value was invalid.",
            data=PresentError(
                code=500,
                description="Flight distance value was invalid.",
                error=str(distance_resp.data),
            ).model_dump(),
        )
    flight_data["fl_distance"] = fl_distance


    # === Open-Meteo API===
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
    # dest-req
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


    # === Type check for model ===
    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:build_ml_model_input")
    model_input_resp = build_ml_model_input(
        flight_data=flight_data,
        origin_weather_data=origin_weather_resp.success,
        dest_weather_data=dest_weather_resp.success,
    )
    if not model_input_resp.ok:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_ml_model_input -- DETAIL: %s", model_input_resp.message)
        code = model_input_resp.code or 500
        message = model_input_resp.message or "Failed to build ML model input."
        return FuncResponse(
            ok=False,
            code=code,
            message=message,
            data=PresentError(
                code=code,
                description=message,
                error=str(model_input_resp.data) if model_input_resp.data is not None else None,
            ).model_dump(),
        )

    if not isinstance(model_input_resp.data, dict):
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:build_ml_model_input -- DETAIL: Model input payload was invalid")
        return FuncResponse(
            ok=False,
            code=500,
            message="ML model input payload was invalid.",
            data=PresentError(
                code=500,
                description="ML model input payload was invalid.",
                error=str(model_input_resp.data),
            ).model_dump(),
        )

    # === Model prediction ===
    logger.info("%(asctime)s -- SERVICE:send_flight__service -- FUNC START:predict_delay_from_model")
    prediction_resp:FuncResponse = predict_delay_from_model(model_input_resp.data)
    if not prediction_resp.ok:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:predict_delay_from_model -- DETAIL: %s", prediction_resp.message)
        code = prediction_resp.code or 500
        message = prediction_resp.message or "Failed to predict flight delay."
        return FuncResponse(
            ok=False,
            code=code,
            message=message,
            data=PresentError(
                code=code,
                description=message,
                error=str(prediction_resp.data) if prediction_resp.data is not None else None,
            ).model_dump(),
        )

    prediction_data = prediction_resp.data
    if not isinstance(prediction_data, dict):
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- FUNC:predict_delay_from_model -- DETAIL: Prediction payload was invalid")
        return FuncResponse(
            ok=False,
            code=500,
            message="Prediction payload was invalid.",
            data=PresentError(
                code=500,
                description="Prediction payload was invalid.",
                error=str(prediction_data),
            ).model_dump(),
        )

    try:
        prediction_response = FlightPredictionResponse(
            is_significant_delay=prediction_data["is_significant_delay"],
            significant_delay_probability=prediction_data["significant_delay_probability"],
            coordinates=FlightDistanceRequest(
                origin_lat=flight_data["origin_lat"],
                origin_long=flight_data["origin_long"],
                dest_lat=flight_data["dest_lat"],
                dest_long=flight_data["dest_long"],
            ),
            distance=FlightDistanceResponse(**distance_resp.data),
            aviationApiData=MatchedAviationAPIDataResponse(**flight_data),
        )
    except (KeyError, TypeError, ValidationError) as e:
        logger.info("%(asctime)s -- SERVICE END:send_flight__service -- DETAIL: Failed to build prediction response -- MESSAGE: %s", str(e))
        return FuncResponse(
            ok=False,
            code=500,
            message="Failed to build prediction response.",
            data=PresentError(
                code=500,
                description="Failed to build prediction response.",
                error=str(e),
            ).model_dump(),
        )
    
    logger.info("%(asctime)s -- SERVICE END:send_flight__service -- DETAIL: Flight delay prediction complete")
    return FuncResponse(
        ok=True,
        code=200,
        message=prediction_resp.message,
        data=prediction_response,
    )
