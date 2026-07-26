import asyncio
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.ml.weather_api_data_pipeline_funcs import run_weather_backfill
from backend.src.logger_config import configure_logging

async def main() -> None:
    configure_logging(Path("backend/logs/weather_ingestion.log"))

    stats = await run_weather_backfill(
        duckdb_path=PROJECT_ROOT/"backend/data/duck_database.duckdb",
        batch_size=50,
        concurrency=10,
    )

    print(stats)

if __name__ == "__main__":
    asyncio.run(main())