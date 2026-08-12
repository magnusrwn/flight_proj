## Overview
BRIEF NOTE ON API

---


### TS '/predict' Request Contract
``` 
export type FlightPredRequest = {
  date: string;
  scheduledDepartureTime: string;
  depIataCode: string;
  destIataCode: string;
};
```
### TS '/predict' Response Contract
Note, this is the 'payload' of the response item. The full response matches the base model 'FuncResponse'
```
export type FlightPredResponse = {
  is_significant_delay: boolean;
  significant_delay_probability: number | null;

  coordinates: {
    origin_lat: number;
    origin_long: number;
    dest_lat: number;
    dest_long: number;
  },
  distance: {
    fl_distance:number;
  }
  aviationApiData: {
    origin:string;
    origin_city_name: string;
    origin_lat: number;
    origin_long: number;
    
    dest: string;
    dest_city_name: string;
    dest_lat: number;
    dest_long: number;

    flight_date: string;
    day_of_month: number;
    day_of_week: number;
    pred_dep_time: number;
    pred_arr_time: number;
    pred_elapsed_time: number;
    year: number;
    month: number;
  }
};
```
---

## Environment Variables
All environment variables are required. To see setup, go [here]() and Ctrl/Cmd + f: '.env Configuration'

---

## Authentication

This is a small scale portfolio project, and thus intended to be run, at this stage, on local host only as being a student I would not love to pay for hosting.

So, there is zero authentication for the backend API, apart from CORS which only allows req's from localhost, if that counts at all.

---

## External API Dependencies

APIs included in API service:
- Open-Meteo weather API
- AviationStack API

AviationStack API gathers the information on the flight, and its schedule. This means that rows can be populated to match the data shape of the flight data in `model_dataset`.

Open-Meteo is used again to father the weather data on the airport handed in. Matching is minimal, as the API is the same method used to gather the data in `model_dataset`.

### AviationStack

**Request AviationStack Service Request:**
```text
Endpoint: "https://api.aviationstack.com/v1/flightsFuture"
params: {
                        // Notes on params:
    access_key: str     // Your API access key
    date: str           // In format YYYY-MM-DD
    iataCode: str       // Must be of length 3, and must be uppercase
    type: str           // Must be "arrival" or departure"
}
```
Note that the notes reflect validation in the project

**Sample AviationStack Service Response:**
```
{
  "pagination": {
    "limit": 100,
    "offset": 0,
    "count": 100,
    "total": 1669022
  },
  "data": [
    [
      {
        "weekday": "7",
        "departure": {
          "iataCode": "BER",
          "icaoCode": "EDDB",
          "terminal": "1",
          "gate": "B17",
          "scheduledTime": "06:15"
        },
        "arrival": {
          "iataCode": "CDG",
          "icaoCode": "LFPG",
          "terminal": "2F",
          "gate": "",
          "scheduledTime": "08:05"
        },
        "aircraft": {
          "modelCode": "BCS3",
          "modelText": "Airbus A220-300"
        },
        "airline": {
          "name": "",
          "iataCode": "AM",
          "icaoCode": "AM"
        },
        "flight": {
          "number": "5748",
          "iataNumber": "AM5748",
          "icaoNumber": "AM5748"
        },
        "codeshared": {
          "airline": {
            "name": "Air France",
            "iataCode": "AF",
            "icaoCode": "AFR"
          },
          "flight": {
            "number": "1135",
            "iataNumber": "AF1135",
            "icaoNumber": "AFR1135"
          }
        }
      }
    ]
  ]
}
```

### Open-Meteo

**Endpoint:** `https://customer-api.open-meteo.com/v1/forecast`
Note that 'customer-' is the endpoint version for customers only (quel suprise)

**Sample Open-Meteo Service Request:**
``` text
method: "GET"
url: "https://customer-api.open-meteo.com/v1/forecast"
params: {
    "apikey": api_key,
    "latitude": lat,
    "longitude": lon,
    "start_date": date.isoformat(),
    "end_date": date.isoformat(),
    "daily":
        "weather_code, temperature_2m_max, temperature_2m_min, apparent_temperature_max,
        apparent_temperature_min, precipitation_sum, rain_sum, showers_sum, snowfall_sum,
        cloud_cover_mean, wind_speed_10m_max, wind_gusts_10m_max,
        wind_direction_10m_dominant, pressure_msl_mean"
    "timezone": "auto",
}
```

**Sample Open-Meteo Service Resposne**
``` text
{
  "latitude": "number",
  "longitude": "number",
  "generationtime_ms": "number",
  "utc_offset_seconds": "number",
  "timezone": "string",
  "timezone_abbreviation": "string",
  "elevation": "number",
  "daily_units": {
    "time": "string",
    "weather_code": "string",
    "temperature_2m_max": "string",
    "temperature_2m_min": "string",
    "apparent_temperature_max": "string",
    "apparent_temperature_min": "string",
    "precipitation_sum": "string",
    "rain_sum": "string",
    "showers_sum": "string",
    "snowfall_sum": "string",
    "cloud_cover_mean": "string",
    "wind_speed_10m_max": "string",
    "wind_gusts_10m_max": "string",
    "wind_direction_10m_dominant": "string",
    "pressure_msl_mean": "string"
  },
  "daily": {
    "time": ["string"],
    "weather_code": ["number"],
    "temperature_2m_max": ["number"],
    "temperature_2m_min": ["number"],
    "apparent_temperature_max": ["number"],
    "apparent_temperature_min": ["number"],
    "precipitation_sum": ["number"],
    "rain_sum": ["number"],
    "showers_sum": ["number"],
    "snowfall_sum": ["number"],
    "cloud_cover_mean": ["number"],
    "wind_speed_10m_max": ["number"],
    "wind_gusts_10m_max": ["number"],
    "wind_direction_10m_dominant": ["number"],
    "pressure_msl_mean": ["number"]
  }
}
```

---

## Testing

Individual relevant functions are tested in `backend/tests`

Main test files regaurding API: `test_weather_api.py`, `test_utils.py`, `test_flight_prediction_service.py`

---

## Error handeling

**Process Backend:**
- Service function runs
- 'ok' set to 'False'
- Errors are collected and pessed up with 'FuncResponse' with codes and messages persisting over layers
- Sent to the frontend

**Process Frontend**
- Recieves response
- Checks 'response.ok'
- If not, expore the error message, code, and data
- Print message, and explain error to user

---

## Future API Work

Any improvements/ todos will be stored [here](https://github.com/magnusrwn/flight_proj/issues) in the issues page.