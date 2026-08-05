import asyncio
from typing import Any, Literal
import httpx
from pydantic import BaseModel
import duckdb as ddb
from pathlib import Path
import sys
import logging

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from src.models.base_models import(
    FuncResponse,
    PresentError,
    RequestWithRetryResponse
)

# ======================================== CONSTS ========================================
DUCKDB_PATH = BACKEND_ROOT/"data/duck_database.duckdb"
logger = logging.getLogger(__name__)

# ======================================== FUNCTIONS ========================================
async def request_with_retry(
    url: str,
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    params: dict[str, Any] | None = None,
    head: dict[str, str] | None = None,
    body: str | list[Any] | bytes | None = None,
    cookies: dict[str, str] | None = None,
    timeout: float = 25.0,
    redirect: bool = True,
    compress: Literal["gzip", "br", "deflate"] | None = None,
    content_type: Literal["application/json", "multipart/form-data"] | None = None,
    idempotency_key: str | None = None,
    request_id: str | None = None,
) -> RequestWithRetryResponse:
    """Make an external HTTP request with retries for temporary failures."""
    max_attempts = 3
    retry_delay_seconds = 3
    retryable_statuses = {408, 429, 500, 502, 503, 504}

    headers = dict(head or {})
    if compress:
        headers.setdefault("Accept-Encoding", compress)
    if content_type:
        headers.setdefault("Content-Type", content_type)
    if idempotency_key:
        headers.setdefault("Idempotency-Key", idempotency_key)
    if request_id:
        headers.setdefault("X-Request-ID", request_id)

    logger.info("%(asctime)s -- REQUESTING: %s\n%s\n%s", url, body, headers)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=redirect,
    ) as client:
        for attempt in range(max_attempts):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params or None,
                    headers=headers or None,
                    content=body,
                    cookies=cookies,
                )
            except httpx.HTTPError as exc:
                if attempt == max_attempts - 1:
                    logger.info("%(asctime)s  REQUEST FAILED -- MAX ATTAMPTS HIT: %s\n%s\n%s", url, body, headers)
                    return RequestWithRetryResponse(
                        error=PresentError(
                            code=408,
                            description="Request failed after retry attempts.",
                            error=str(exc),
                        )
                    )

                # Backoff prevents a burst of retries from worsening a rate limit.
                await asyncio.sleep(retry_delay_seconds * (2**attempt))
                logger.info("%(asctime)s -- RETRY-COUNT %s RETRYING REQUEST: %s\n%s\n%s", attempt, url, body, headers)
                continue

            if response.is_success:
                logger.info("%(asctime)s -- RESPONSE SUCCESS: %s\n%s\n%s", url, body, headers)
                try:
                    payload = response.json()
                    logger.info("%(asctime)s -- EXTRACTED RESPONSE: %s\n%s\n%s", url, body, headers)
                except ValueError:
                    payload = {"content": response.text}

                if isinstance(payload, dict):
                    return RequestWithRetryResponse(success=payload)
                return RequestWithRetryResponse(success={"data": payload})

            if response.status_code not in retryable_statuses or attempt == max_attempts - 1:
                logger.info("%(asctime)s -- REQUEST FAILED WITH STATUS CODE %s OR HIT MAX RETRYS: %s\n%s\n%s", str(response.status_code), url, body, headers)
                return RequestWithRetryResponse(
                    error=PresentError(
                        code=int(response.status_code),
                        description=f"Request hit bad status code, or hit retry limit",
                        error=str(response.text),
                    )
                )

            await asyncio.sleep(retry_delay_seconds * (2**attempt))

    # The loop always returns; this keeps the type contract explicit for linters.
    logger.info("%(asctime)s -- REQUEST WITH RETRY ENDED UNEXPECTEDLY: %s\n%s\n%s", url, body, headers)
    return RequestWithRetryResponse(
        error=PresentError(code=500, description="Uncaught error in 'request_with_retry'")
    )

def is_in_table(table_name:str, column:str, airprot_code:str) -> FuncResponse:
    con = None
    try:
        con = ddb.connect(DUCKDB_PATH)
        logger.info("%(asctime)s -- CONNECTED TO DUCK-DB")

        r = con.execute(f"""
            SELECT EXISTS(
            SELECT 1
            from {table_name}
            WHERE {column} = ?
            )
        """,
        [airprot_code]
        ).fetchone()

        logger.info("%(asctime)s -- READ DUCK-DB TABLE:%s, COLUMN:%s, FOR: %s", table_name, column, airprot_code)
        return FuncResponse(
            ok=True,
            data=r[0]
        )
    except ddb.ConnectionException as e:
        logger.info("%(asctime)s -- HIT DUCK-DB EXCEPTION -- INFO: %s", str(e))
        return FuncResponse(
            ok=False, code=500, message="Failed to connect to duckdb with given connection path", data=str(e)
        )
    except (ddb.CatalogException, ddb.BinderException) as e:
        logger.info("%(asctime)s -- HIT DUCK-DB EXCEPTION -- INFO: %s", str(e))
        return FuncResponse(
            ok=False, code=400, message="Incorrect duckdb-SQL fields passed. Table or Col does not exist", data=str(e)
        )    
    finally:
        if con != None:
            con.close()
            logger.info("%(asctime)s -- CLOSED DUCK-DB")

