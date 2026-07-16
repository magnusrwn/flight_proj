import json
import csv
import pandas as pd
from httpx import AsyncClient, HTTPError
import asyncio

AIRPORT_DATA_PATH = './data/airports_sorted.csv'
BASE_API_URL = 'https://archive-api.open-meteo.com/v1/archive'

with open(AIRPORT_DATA_PATH, newline="") as f:
    reader = csv.DictReader(f)
    # Create data rows var
    DATA_ROWS_IN = list(reader)

async def fetch_weather_data(date:str, long:str, lat:str, code:str):
    async with AsyncClient() as client:
        url = f"{BASE_API_URL}?latitude={lat}&longitude={long}&start_date={date}&end_date={date}&daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,snow_depth_max,cloud_cover_mean,cloud_cover_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,pressure_msl_mean,visibility_mean&timezone=auto"
        try:
            response = await client.get(url=url)
            print(response)
            return response
        except HTTPError as e:
            print(f'Error in weather API request.\nDate:{date}, Airport:{code}\n\nError: {e}')
            return


# I WANT TO KEEP: ["daily", "daily_units", "latitude", "longitude"]
async def main():
    # create all the async tasks here...
    pass

# Runner
asyncio.run(main())

