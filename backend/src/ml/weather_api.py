import json
import csv
import pandas as pd
from httpx import AsyncClient, HTTPError, 
import asyncio
from backend.src.utils.helper import request_with_retry

AIRPORT_DATA_PATH = './data/airports_sorted.csv'
BASE_API_URL = 'https://archive-api.open-meteo.com/v1/archive'

with open(AIRPORT_DATA_PATH, newline="") as f:
    reader = csv.DictReader(f)
    # Create data rows var
    DATA_ROWS_IN = list(reader)

async def fetch_weather_data(queue, date:str, long:str, lat:str, code:str):
    async with AsyncClient() as client:
        url = f"{BASE_API_URL}?latitude={lat}&longitude={long}&start_date={date}&end_date={date}&daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,snow_depth_max,cloud_cover_mean,cloud_cover_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,pressure_msl_mean,visibility_mean&timezone=auto"
        try:
            response = await request_with_retry() # format the things needed to send in the request

            if response["success"]:
                await queue.put(response["success"])

            elif response["error"]:
                # fugure
                pass
            else: # rep == Nul
                # LOG ERR
                pass
            
            # handle potential error
            # follow up how responses are savd from the tasks... will i have a list/ dict of responses with a few errs in there? (ideal)
        
        except HTTPError as e:
            # LOG ERROR HERE! ASK ON LOGGING
            # print(f'Error in weather API request.\nDate:{date}, Airport:{code}\n\nError: {e}')
            # figure better err handeling, as I may not need failed rows... they could just be disgaurded if they fail again and again and again
            return

async def writer(queue):
    async with writer as w:
        while True:
            # row = queue.get()...
            pass

# I WANT TO KEEP: ["daily", "daily_units", "latitude", "longitude"]
async def main():
    queue = asyncio.Queue()
    # create all the async tasks here...
    

# Runner
asyncio.run(main())

