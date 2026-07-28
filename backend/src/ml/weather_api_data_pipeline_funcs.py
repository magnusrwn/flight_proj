import asyncio
import json
from urllib.parse import urlencode
from pydantic import BaseModel
from datetime import date
from pathlib import Path
from typing import Any
import duckdb as ddb
from backend.src.utils import request_with_retry, RequestWithRetryResponse
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

OPEN_METEO_ARCHIVE_URL = "https://customer-archive-api.open-meteo.com/v1/archive"
QUEUE_TABLE_NAME = "weather_req_table"
RAW_TABLE_NAME= "weather_response_raw"

class WeatherPipelineStats(BaseModel):
    queued: int = 0
    claimed: int = 0
    fetched: int = 0
    written: int = 0
    failed_fetch: int = 0
    failed_write: int = 0

def ensure_weather_raw_table(con:ddb.DuckDBPyConnection):
    con.sql(f"""
        CREATE TABLE IF NOT EXISTS {RAW_TABLE_NAME} (
            code VARCHAR NOT NULL,
            date DATE NOT NULL,
            api_url VARCHAR NOT NULL,
            fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            payload JSON,
            PRIMARY KEY (code, date)
        )
    """)

def build_weather_request_url(lat: float, lon: float, date: date) -> str:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date.isoformat(),
        "end_date": date.isoformat(),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_sum",
                "rain_sum",
                "showers_sum",
                "snowfall_sum",
                "cloud_cover_mean",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
                "pressure_msl_mean",
            ]
        ),
        "timezone": "auto",
    }
    return f"{OPEN_METEO_ARCHIVE_URL}?{urlencode(params)}&apikey={os.getenv('OPEN_METEO_API_KEY')}"

def claim_next_batch(con:ddb.DuckDBPyConnection, *, batch_size: int) -> list[dict[str, Any]]:
    rows = con.execute(
        f"""
        WITH claimed AS (
            SELECT code, date, lat, long
            FROM {QUEUE_TABLE_NAME}
            WHERE status = 'pending'
            ORDER BY date, code
            LIMIT ?
        )
        UPDATE {QUEUE_TABLE_NAME} q
        SET status = 'in_progress',
            attempt_count = COALESCE(attempt_count, 0) + 1,
            updated_at = CURRENT_TIMESTAMP
        FROM claimed
        WHERE q.code = claimed.code
          AND q.date = claimed.date
        RETURNING q.code, q.date, q.lat, q.long
        """,
        [batch_size],
    ).fetchall()
    return [
        {"code": row[0], "date": row[1], "lat": row[2], "lon": row[3]}
        for row in rows
    ]

def reset_stuck_in_progress_rows(con: ddb.DuckDBPyConnection) -> int:
    """
    Requeues rows that were claimed but never completed, usually because the
    process crashed while they were in progress.
    """
    rows = con.execute(
        f"""
        UPDATE {QUEUE_TABLE_NAME}
        SET status = 'pending',
            updated_at = CURRENT_TIMESTAMP
        WHERE status = 'in_progress'
          AND updated_at < CURRENT_TIMESTAMP - INTERVAL '1 minutes'
        RETURNING code, date
        """
    ).fetchall()
    return len(rows)

def mark_queue_row(
    con: ddb.DuckDBPyConnection,
    *,
    queue_table_name: str,
    code: str,
    date: date,
    status: str,
    last_error: str | None = None,
    # raw_payload: dict[str, Any] | None = None,
) -> None:
    '''
    Updates the 'status' field of items on 'weather_req_table'(duckdb)
    '''
    con.execute(
        f"""
        UPDATE {queue_table_name}
        SET status = ?,
            last_error = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE code = ?
            AND date = ?
        """,
        [status, last_error, code, date],
    )

def write_raw_weather_row(
    con: ddb.DuckDBPyConnection,
    *,
    table_name: str,
    code: str,
    date: date,
    api_url: str,
    payload: dict[str, Any],
) -> None:
    con.execute(
        f"""
        INSERT INTO {table_name} (code, date, api_url, payload)
        VALUES (?, ?, ?, ?::JSON)
        ON CONFLICT (code, date) DO UPDATE SET
            fetched_at = now(),
            api_url = excluded.api_url,
            payload = excluded.payload
        """,
        [code, date, api_url, json.dumps(payload)],
    )

async def fetch_and_persist_one(
    con: ddb.DuckDBPyConnection,
    *,
    code: str,
    date: date,
    lat: float,
    lon: float,
    stats: WeatherPipelineStats,
    db_lock: asyncio.Lock,
) -> None:
    url = build_weather_request_url(lat=lat, lon=lon, date=date)
    response: RequestWithRetryResponse = await request_with_retry(url, "GET")
    stats.fetched += 1

    try:
        if response.error is not None or response.success is None:
            stats.failed_fetch += 1
            async with db_lock:
                mark_queue_row(
                    con,
                    queue_table_name=QUEUE_TABLE_NAME,
                    code=code,
                    date=date,
                    status="failed",
                    last_error=(response.error.error if response.error else "missing payload"),
                )
            return

        payload = response.success
        async with db_lock:
            write_raw_weather_row(
                con,
                table_name=RAW_TABLE_NAME,
                code=code,
                date=date,
                api_url=url,
                payload=payload,
            )
            mark_queue_row(
                con,
                queue_table_name=QUEUE_TABLE_NAME,
                code=code,
                date=date,
                status="done"
            )
        stats.written += 1
        if int(stats.written) % 500 == 0:
            logger.info("Successfully written %s rows", stats.written)
    except Exception as exc:
        stats.failed_write += 1
        async with db_lock:
            mark_queue_row(
                con,
                queue_table_name=QUEUE_TABLE_NAME,
                code=code,
                date=date,
                status="failed",
                last_error=str(exc),
            )
        raise

async def run_weather_backfill(
    *,
    duckdb_path: str | Path,
    batch_size: int = 50,
    concurrency: int = 10,
) -> WeatherPipelineStats:
    stats = WeatherPipelineStats()
    con: ddb.DuckDBPyConnection | None = None
    try:
        logger.info("Connecting to duckdb")
        con = ddb.connect(str(duckdb_path))
        logger.info("Connected to duckdb")

        ensure_weather_raw_table(con)
        logger.info("Ensured weather_raw table")
        
        deleted_rows = reset_stuck_in_progress_rows(con)
        logger.info("Reset %s rows to 'pending'", deleted_rows)

        semaphore = asyncio.Semaphore(concurrency)
        db_lock = asyncio.Lock()

        batch_num: int = 0
        while True:
            batch = claim_next_batch(con, batch_size=batch_size)

            if not batch:
                break
            batch_num += 1
            stats.claimed += len(batch)
            logger.info("Claimed %s in batch no:%s", len(batch), batch_num)

            async def _run_task(row: dict[str, Any]) -> None:
                async with semaphore:
                    await fetch_and_persist_one(
                        con=con,
                        code=row["code"],
                        date=row["date"],
                        lat=row["lat"],
                        lon=row["lon"],
                        stats=stats,
                        db_lock=db_lock,
                    )

            await asyncio.gather(*[_run_task(row) for row in batch])
        return stats
    finally:
        if con is not None:
            con.close()
            logger.info("Connection closed")
            
        logger.info(
            "Process terminated: claimed=%s fetched=%s written=%s failed_fetch=%s failed_write=%s",
            stats.claimed,
            stats.fetched,
            stats.written,
            stats.failed_fetch,
            stats.failed_write
        )


def create_model_dataset(duck_db_path: str | Path) -> None:
    con: ddb.DuckDBPyConnection | None = None
    try:
        con = ddb.connect(str(duck_db_path))

        logger.info("STARTING RAW_FLIGHT_DATA_MERGE")

        con.sql("""
            CREATE OR REPLACE TABLE model_dataset AS
            SELECT
                f.date AS flight_date,
                f.origin AS origin,
                f.dest AS dest,

                CAST(origin_weather.payload->'daily'->'weather_code'->>0 AS DOUBLE) AS origin_weather_code,
                CAST(origin_weather.payload->'daily'->'temperature_2m_max'->>0 AS DOUBLE) AS origin_temperature_2m_max,
                CAST(origin_weather.payload->'daily'->'temperature_2m_min'->>0 AS DOUBLE) AS origin_temperature_2m_min,
                CAST(origin_weather.payload->'daily'->'apparent_temperature_max'->>0 AS DOUBLE) AS origin_apparent_temperature_max,
                CAST(origin_weather.payload->'daily'->'apparent_temperature_min'->>0 AS DOUBLE) AS origin_apparent_temperature_min,
                CAST(origin_weather.payload->'daily'->'precipitation_sum'->>0 AS DOUBLE) AS origin_precipitation_sum,
                CAST(origin_weather.payload->'daily'->'rain_sum'->>0 AS DOUBLE) AS origin_rain_sum,
                CAST(origin_weather.payload->'daily'->'showers_sum'->>0 AS DOUBLE) AS origin_showers_sum,
                CAST(origin_weather.payload->'daily'->'snowfall_sum'->>0 AS DOUBLE) AS origin_snowfall_sum,
                CAST(origin_weather.payload->'daily'->'cloud_cover_mean'->>0 AS DOUBLE) AS origin_cloud_cover_mean,
                CAST(origin_weather.payload->'daily'->'wind_speed_10m_max'->>0 AS DOUBLE) AS origin_wind_speed_10m_max,
                CAST(origin_weather.payload->'daily'->'wind_gusts_10m_max'->>0 AS DOUBLE) AS origin_wind_gusts_10m_max,
                CAST(origin_weather.payload->'daily'->'wind_direction_10m_dominant'->>0 AS DOUBLE) AS origin_wind_direction_10m_dominant,
                CAST(origin_weather.payload->'daily'->'pressure_msl_mean'->>0 AS DOUBLE) AS origin_pressure_msl_mean,

                CAST(dest_weather.payload->'daily'->'weather_code'->>0 AS DOUBLE) AS dest_weather_code,
                CAST(dest_weather.payload->'daily'->'temperature_2m_max'->>0 AS DOUBLE) AS dest_temperature_2m_max,
                CAST(dest_weather.payload->'daily'->'temperature_2m_min'->>0 AS DOUBLE) AS dest_temperature_2m_min,
                CAST(dest_weather.payload->'daily'->'apparent_temperature_max'->>0 AS DOUBLE) AS dest_apparent_temperature_max,
                CAST(dest_weather.payload->'daily'->'apparent_temperature_min'->>0 AS DOUBLE) AS dest_apparent_temperature_min,
                CAST(dest_weather.payload->'daily'->'precipitation_sum'->>0 AS DOUBLE) AS dest_precipitation_sum,
                CAST(dest_weather.payload->'daily'->'rain_sum'->>0 AS DOUBLE) AS dest_rain_sum,
                CAST(dest_weather.payload->'daily'->'showers_sum'->>0 AS DOUBLE) AS dest_showers_sum,
                CAST(dest_weather.payload->'daily'->'snowfall_sum'->>0 AS DOUBLE) AS dest_snowfall_sum,
                CAST(dest_weather.payload->'daily'->'cloud_cover_mean'->>0 AS DOUBLE) AS dest_cloud_cover_mean,
                CAST(dest_weather.payload->'daily'->'wind_speed_10m_max'->>0 AS DOUBLE) AS dest_wind_speed_10m_max,
                CAST(dest_weather.payload->'daily'->'wind_gusts_10m_max'->>0 AS DOUBLE) AS dest_wind_gusts_10m_max,
                CAST(dest_weather.payload->'daily'->'wind_direction_10m_dominant'->>0 AS DOUBLE) AS dest_wind_direction_10m_dominant,
                CAST(dest_weather.payload->'daily'->'pressure_msl_mean'->>0 AS DOUBLE) AS dest_pressure_msl_mean
            FROM flight_data AS f
            LEFT JOIN weather_response_raw AS origin_weather
                ON origin_weather.date = f.date
                AND origin_weather.code = f.origin
            LEFT JOIN weather_response_raw AS dest_weather
                ON dest_weather.date = f.date
                AND dest_weather.code = f.dest
        """)

        row_count = con.sql("SELECT COUNT(*) FROM model_dataset").fetchone()[0]
        logger.info("created model_dataset with %s rows", row_count)
    finally:
        if con is not None:
            con.close()
            logger.info("Duckdb closed. Data ready for training")
