from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import duckdb as ddb
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from utils import request_with_retry, RequestWithRetryResponse

logger = logging.getLogger(__name__)

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


@dataclass(frozen=True)
class WeatherRequestKey:
    airport_code: str
    request_date: date


@dataclass
class WeatherPipelineStats:
    queued: int = 0
    claimed: int = 0
    fetched: int = 0
    written: int = 0
    failed_fetch: int = 0
    failed_write: int = 0


def build_weather_request_url(*, lat: float, lon: float, request_date: date) -> str:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": request_date.isoformat(),
        "end_date": request_date.isoformat(),
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
                "snow_depth_max",
                "cloud_cover_mean",
                "cloud_cover_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
                "pressure_msl_mean",
                "visibility_mean",
            ]
        ),
        "timezone": "auto",
    }
    return f"{OPEN_METEO_ARCHIVE_URL}?{urlencode(params)}"


def ensure_weather_queue_table(con: ddb.DuckDBPyConnection, table_name: str = "weather_request_queue") -> None:
    con.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            airport_code VARCHAR NOT NULL,
            request_date DATE NOT NULL,
            lat DOUBLE NOT NULL,
            lon DOUBLE NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'pending',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error VARCHAR,
            raw_payload VARCHAR,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (airport_code, request_date)
        )
        """
    )


def ensure_weather_raw_table(con: ddb.DuckDBPyConnection, table_name: str = "weather_raw") -> None:
    con.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            airport_code VARCHAR NOT NULL,
            request_date DATE NOT NULL,
            fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            api_url VARCHAR NOT NULL,
            payload JSON,
            PRIMARY KEY (airport_code, request_date)
        )
        """
    )


def enqueue_weather_requests(
    con: ddb.DuckDBPyConnection,
    request_table_name: str,
    queue_table_name: str = "weather_request_queue",
) -> int:
    ensure_weather_queue_table(con, queue_table_name)
    inserted = con.sql(
        f"""
        INSERT INTO {queue_table_name} (airport_code, request_date, lat, lon)
        SELECT DISTINCT
            code AS airport_code,
            date AS request_date,
            lat,
            long AS lon
        FROM {request_table_name}
        ON CONFLICT (airport_code, request_date) DO NOTHING
        """
    ).fetchone()[0]
    return int(inserted or 0)


def claim_next_batch(db: Session, *, batch_size: int, queue_table_name: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            f"""
            WITH claimed AS (
                SELECT airport_code, request_date, lat, lon
                FROM {queue_table_name}
                WHERE status = 'pending'
                ORDER BY request_date, airport_code
                LIMIT :batch_size
            )
            UPDATE {queue_table_name} q
            SET status = 'in_progress',
                attempt_count = attempt_count + 1,
                updated_at = CURRENT_TIMESTAMP
            FROM claimed
            WHERE q.airport_code = claimed.airport_code
              AND q.request_date = claimed.request_date
            RETURNING q.airport_code, q.request_date, q.lat, q.lon
            """
        ),
        {"batch_size": batch_size},
    ).mappings().all()
    db.commit()
    return [dict(row) for row in rows]


def mark_queue_row(
    db: Session,
    *,
    queue_table_name: str,
    airport_code: str,
    request_date: date,
    status: str,
    last_error: str | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> None:
    db.execute(
        text(
            f"""
            UPDATE {queue_table_name}
            SET status = :status,
                last_error = :last_error,
                raw_payload = :raw_payload,
                updated_at = CURRENT_TIMESTAMP
            WHERE airport_code = :airport_code
              AND request_date = :request_date
            """
        ),
        {
            "status": status,
            "last_error": last_error,
            "raw_payload": json.dumps(raw_payload) if raw_payload is not None else None,
            "airport_code": airport_code,
            "request_date": request_date,
        },
    )
    db.commit()


def write_raw_weather_row(
    con: ddb.DuckDBPyConnection,
    *,
    table_name: str,
    airport_code: str,
    request_date: date,
    api_url: str,
    payload: dict[str, Any],
) -> None:
    con.execute(
        f"""
        INSERT INTO {table_name} (airport_code, request_date, api_url, payload)
        VALUES (?, ?, ?, ?::JSON)
        ON CONFLICT (airport_code, request_date) DO UPDATE SET
            fetched_at = CURRENT_TIMESTAMP,
            api_url = excluded.api_url,
            payload = excluded.payload
        """,
        [airport_code, request_date, api_url, json.dumps(payload)],
    )


def flatten_daily_weather_payload(payload: dict[str, Any]) -> dict[str, Any]:
    daily = payload.get("daily") or {}
    flattened: dict[str, Any] = {}
    for key, value in daily.items():
        flattened[f"daily_{key}"] = value[0] if isinstance(value, list) and value else value
    return flattened


async def fetch_and_persist_one(
    *,
    db_factory,
    con: ddb.DuckDBPyConnection,
    raw_table_name: str,
    queue_table_name: str,
    airport_code: str,
    request_date: date,
    lat: float,
    lon: float,
    stats: WeatherPipelineStats,
) -> None:
    url = build_weather_request_url(lat=lat, lon=lon, request_date=request_date)
    response: RequestWithRetryResponse = await request_with_retry(url, "GET")
    stats.fetched += 1

    db = db_factory()
    try:
        if response.error is not None or response.success is None:
            stats.failed_fetch += 1
            mark_queue_row(
                db,
                queue_table_name=queue_table_name,
                airport_code=airport_code,
                request_date=request_date,
                status="failed",
                last_error=(response.error.error if response.error else "missing payload"),
            )
            return

        payload = response.success
        write_raw_weather_row(
            con,
            table_name=raw_table_name,
            airport_code=airport_code,
            request_date=request_date,
            api_url=url,
            payload=payload,
        )
        mark_queue_row(
            db,
            queue_table_name=queue_table_name,
            airport_code=airport_code,
            request_date=request_date,
            status="done",
            raw_payload=payload,
        )
        stats.written += 1
    except Exception as exc:
        stats.failed_write += 1
        mark_queue_row(
            db,
            queue_table_name=queue_table_name,
            airport_code=airport_code,
            request_date=request_date,
            status="failed",
            last_error=str(exc),
        )
        raise
    finally:
        db.close()


async def run_weather_backfill(
    *,
    duckdb_path: str | Path,
    queue_table_name: str = "weather_request_queue",
    raw_table_name: str = "weather_raw",
    batch_size: int = 50,
    concurrency: int = 10,
) -> WeatherPipelineStats:
    con = ddb.connect(str(duckdb_path))
    ensure_weather_queue_table(con, queue_table_name)
    ensure_weather_raw_table(con, raw_table_name)

    stats = WeatherPipelineStats()
    semaphore = asyncio.Semaphore(concurrency)

    def db_factory():
        return next(get_db())

    while True:
        db = db_factory()
        try:
            batch = claim_next_batch(db, batch_size=batch_size, queue_table_name=queue_table_name)
        finally:
            db.close()

        if not batch:
            break

        stats.claimed += len(batch)

        async def _run_task(row: dict[str, Any]) -> None:
            async with semaphore:
                await fetch_and_persist_one(
                    db_factory=db_factory,
                    con=con,
                    raw_table_name=raw_table_name,
                    queue_table_name=queue_table_name,
                    airport_code=row["airport_code"],
                    request_date=row["request_date"],
                    lat=row["lat"],
                    lon=row["lon"],
                    stats=stats,
                )

        await asyncio.gather(*[_run_task(row) for row in batch])

    return stats


def build_flight_weather_join(
    con: ddb.DuckDBPyConnection,
    *,
    flights_table: str,
    weather_clean_table: str,
    output_table: str = "flights_enriched",
) -> None:
    con.sql(
        f"""
        CREATE OR REPLACE TABLE {output_table} AS
        SELECT
            f.*,
            ow.daily_weather_code AS origin_weather_code,
            ow.daily_temperature_2m_max AS origin_weather_temp_max,
            ow.daily_temperature_2m_min AS origin_weather_temp_min,
            dw.daily_weather_code AS dest_weather_code,
            dw.daily_temperature_2m_max AS dest_weather_temp_max,
            dw.daily_temperature_2m_min AS dest_weather_temp_min
        FROM {flights_table} f
        LEFT JOIN {weather_clean_table} ow
            ON ow.airport_code = f.origin
           AND ow.request_date = f.date
        LEFT JOIN {weather_clean_table} dw
            ON dw.airport_code = f.dest
           AND dw.request_date = f.date
        """
    )
