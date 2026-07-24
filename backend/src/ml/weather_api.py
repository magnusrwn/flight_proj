# NOTE: Migrate everything to SQL for this step and beyond

# import csv
# import logging
# import time
# from dataclasses import dataclass
# import asyncio
# from pathlib import Path
# import sys
# import pandas as pd
# # Here evrything must be set to the project root. As when ran as an independant file, imports are relative, which causes pain.
# PROJ_ROOT = Path(__file__).parents[3]
# sys.path.insert(0, str(PROJ_ROOT))

# from backend.src.logger_config import configure_logging
# from backend.src.utils import request_with_retry, RequestWithRetryResponse

# DATA_DIR = PROJ_ROOT/"backend/data"
# OUTPUT_CSV = DATA_DIR / "output/flights_airports_weather.csv"

# LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
# AIRPORTS_WITH_DATES_PATH = DATA_DIR / "airport/airport_data_for_weather_api.csv"

# with open(AIRPORTS_WITH_DATES_PATH, newline="") as f:
#     reader = csv.DictReader(f)
#     # Create data rows var
#     DATA_ROWS = list(reader)

# logger = logging.getLogger(__name__)

# BASE_API_URL = 'https://archive-api.open-meteo.com/v1/archive'

# API_DAILY_FIELDS = [
#     "time",
#     "weather_code",
#     "temperature_2m_max",
#     "temperature_2m_min",
#     "apparent_temperature_max",
#     "apparent_temperature_min",
#     "precipitation_sum",
#     "rain_sum",
#     "showers_sum",
#     "snowfall_sum",
#     "snow_depth_max",
#     "cloud_cover_mean",
#     "cloud_cover_max",
#     "wind_speed_10m_max",
#     "wind_gusts_10m_max",
#     "wind_direction_10m_dominant",
#     "pressure_msl_mean",
#     "visibility_mean",
# ]

# FIELDNAMES = (
#     ["date", "airport_code"]
#     + [f"daily_{field}" for field in API_DAILY_FIELDS]
# )

# @dataclass
# class RunStats:
#     enqueued: int = 0
#     fetch_failed: int = 0
#     written: int = 0
#     write_failed: int = 0
#     already_written: int = 0

# def load_completed_and_remove_dupes() -> set:
#     completed = set()
#     if OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0:

#         # If the output has rows, furst delete all dupes, and re-write before reading
#         data = pd.read_csv(OUTPUT_CSV)
#         rows_before: int = len(data)

#         data = data.drop_duplicates(subset=["date", "airport_code"])
#         rows_after: int = len(data)
#         logger.info(f"Dropped {rows_before - rows_after} rows. (Duplicates)")

#         # re-write the csv.
#         data.to_csv(OUTPUT_CSV, index=False)

#         # Open/ read
#         with open(OUTPUT_CSV, newline="", encoding="utf-8") as file:
#             for row in csv.DictReader(file):
#                 completed.add((row["date"], row["airport_code"]))

#     return completed

# async def fetch_weather_data(queue: asyncio.Queue[RequestWithRetryResponse], date: str, long: str, lat: str, airport_code:str, stats: RunStats, completed:set):
#     url = f"{BASE_API_URL}?latitude={lat}&longitude={long}&start_date={date}&end_date={date}&daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,snow_depth_max,cloud_cover_mean,cloud_cover_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,pressure_msl_mean,visibility_mean&timezone=auto"

#     if (date, airport_code) in completed:
#         stats.already_written += 1
#         return None

    
#     try:
#         response = await request_with_retry(url, "GET")
#         queue_item = {
#             "response":response,
#             "date":date,
#             "airport_code":airport_code
#         }
#         await queue.put(queue_item)
#         stats.enqueued += 1
        
#     except Exception:
#         stats.fetch_failed += 1
#         logger.exception(
#             "Unexpected fetch error: date=%s latitude=%s longitude=%s",
#             date,
#             airport_code
#         )

# async def writer(queue: asyncio.Queue[RequestWithRetryResponse], stats: RunStats, completed:set):
#     with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as file:
#         csv_writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
#         file_exists = OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0
#         if not file_exists:
#             csv_writer.writeheader()
        
#         while True:
#             queue_item = await queue.get()
#             item_response = queue_item.get("response", {})
#             item_date = queue_item.get("date", "")
#             item_airport_code = queue_item.get("airport_code", "")
#             try:
#                 # Assure responses
#                 if item_response.error is not None:
#                     stats.fetch_failed += 1
#                     logger.warning("Skipping failed weather response: %s", item_response.error)
#                     continue
#                 # if there is no data under the success key, then also add it to the error log count.
#                 if item_response.success is None:
#                     stats.fetch_failed += 1
#                     logger.warning("Skipping weather response with no payload")
#                     continue

#                 # Extract payload on success
#                 payload = item_response.success
#                 daily = payload.get("daily", {})

#                 if (item_date, item_airport_code, long := payload.get("longitude"),lat := payload.get("latitude")) in completed:
#                     logger.info("Found dupe being written")
#                     continue

#                 row = {
#                     "date": item_date,
#                     "airport_code": item_airport_code
#                 }
#                 row.update(
#                     {
#                         f"daily_{field}": values[0]
#                         if isinstance(values := daily.get(field), list) and values else values
#                         for field in API_DAILY_FIELDS
#                     }
#                 )

#                 csv_writer.writerow(row)
#                 stats.written += 1
#             except Exception:
#                 stats.write_failed += 1
#                 logger.exception("Could not write weather response to CSV")
#             finally:
#                 queue.task_done()

# async def main():
#     # Prep logger
#     configure_logging(LOG_DIR/"weather_api.log")
#     started_at = time.monotonic()
#     queue = asyncio.Queue()
#     stats = RunStats()
#     logger.info("Starting weather-data run: input_rows=%d output=%s", len(DATA_ROWS), OUTPUT_CSV)

#     # load all currently completed
#     completed = load_completed_and_remove_dupes()

#     # Creates and starts API req tasks
#     fetch_tasks = [
#         asyncio.create_task(
#             fetch_weather_data(queue, row["fl_date"], row["long"], row["lat"], row["airport_code"], stats, completed)
#         ) for row in DATA_ROWS
#     ]
    
#     # Creates and starts the writer
#     writer_task = asyncio.create_task(writer(queue, stats, completed))


#     await asyncio.gather(*fetch_tasks)
#     # Ensure task count in queue is == 0
#     await queue.join()

#     # Cancel the writer running
#     writer_task.cancel()

#     # Ensure the writer is closed
#     try:
#         # Wait till its done
#         await writer_task
#     except asyncio.CancelledError:
#         logger.info("Writer cancelled as expected.")
#         pass

#     # Calculate the elapsed seconds
#     elapsed_seconds = time.monotonic() - started_at
#     # Log it all
#     logger.info(
#         "Weather-data run complete: enqueued=%d written=%d fetch_failed=%d "
#         "write_failed=%d elapsed_seconds=%.2f",
#         stats.enqueued,
#         stats.written,
#         stats.fetch_failed,
#         stats.write_failed,
#         elapsed_seconds,
#     )

# # Run
# if __name__ == '__main__':
#     asyncio.run(main())
