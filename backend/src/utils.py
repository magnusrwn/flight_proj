import asyncio
from typing import Any, Literal
import httpx
from pydantic import BaseModel, Field
import duckdb as ddb
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
from src.models.base_models import FuncResponse

# ======================================== CONSTS ========================================
DUCKDB_PATH = BACKEND_ROOT/"data/duck_database.duckdb"

# ======================================== MODELS ========================================
class PresentError(BaseModel):
    description: str
    error: str | None = None

class RequestWithRetryResponse(BaseModel):
    success: dict[str, Any] | None = None
    error: PresentError | None = None

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
                    return RequestWithRetryResponse(
                        error=PresentError(
                            description="Request failed after retry attempts.",
                            error=str(exc),
                        )
                    )

                # Backoff prevents a burst of retries from worsening a rate limit.
                await asyncio.sleep(retry_delay_seconds * (2**attempt))
                continue

            if response.is_success:
                try:
                    payload = response.json()
                except ValueError:
                    payload = {"content": response.text}

                if isinstance(payload, dict):
                    return RequestWithRetryResponse(success=payload)
                return RequestWithRetryResponse(success={"data": payload})

            if response.status_code not in retryable_statuses or attempt == max_attempts - 1:
                return RequestWithRetryResponse(
                    error=PresentError(
                        description=f"Request returned HTTP {response.status_code}.",
                        error=response.text,
                    )
                )

            await asyncio.sleep(retry_delay_seconds * (2**attempt))

    # The loop always returns; this keeps the type contract explicit for linters.
    return RequestWithRetryResponse(
        error=PresentError(description="Request ended unexpectedly.")
    )

def is_in_table_(table_name:str, column:str, airprot_code:str) -> FuncResponse:
    con = None
    try:
        con = ddb.connect(DUCKDB_PATH)
        r = con.execute(f"""
            SELECT EXISTS(
            SELECT 1
            from {table_name}
            WHERE {column} = ?
            )
        """,
        [airprot_code]
        ).fetchone()

        return FuncResponse(
            ok=True,
            data={"exist":r[0]}
        )

    except ddb.ConnectionException as e:
        # NOTE: Log
            return FuncResponse(
                ok=False,
                error={
                    "message":"Duckdb path configured incorrect, and/or could not connect to duckdb. Find 'path' to view.",
                    "error":str(e),
                    "path":DUCKDB_PATH
                }
            )
    except (ddb.CatalogException, ddb.BinderException) as e:
            # NOTE: Log
            return FuncResponse(
                ok=False,
                error={
                    "message":"Incorrect duckdb SQL fields passed. Table or Col does not exist",
                    "error":str(e)
                }
            )    
    finally:
        if con != None:
            con.close()

