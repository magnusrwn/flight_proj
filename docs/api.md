# API Reference

The backend is a FastAPI application defined in [`backend/src/main.py`](../backend/src/main.py). When running locally, its base URL is `http://localhost:8000`.

The API has two routes:

- [`GET /health`](#get-health) checks that the application is running.
- [`POST /predict`](#post-predict) builds a feature row and returns a flight-delay prediction.

## Environment Variables

Create the files from the repository templates:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Backend

| Variable | Required | Purpose |
| --- | --- | --- |
| `AVIATION_STACK_API_KEY` | Yes | Authenticates requests to AviationStack's scheduled-flight endpoint. |
| `OPEN_METEO_API_KEY` | Yes | Authenticates requests to Open-Meteo's customer forecast endpoint. |

This project is configured for paid/customer API access:

- AviationStack: `/predict` calls `https://api.aviationstack.com/v1/flightsFuture`. AviationStack's pricing page lists future-flight access under paid plans, so expect to need a paid AviationStack plan for the configured workflow.
- Open-Meteo: the code calls `https://customer-api.open-meteo.com/v1/forecast` with an API key. Open-Meteo's free open-access API is for non-commercial use and uses a different no-key endpoint with rate limits. The customer endpoint requires a subscription API key.

If a backend key is missing, the route returns a `500` response with a `detail.description` such as `AVIATION_STACK_API_KEY is not configured.` or `OPEN_METEO_API_KEY is not configured.`.

### Frontend

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL. |
| `VITE_PREDICTION_ENDPOINT` | `/predict` | Prediction route appended to the base URL. |

The frontend reads Vite variables at build time. Keep the backend and frontend `.env` files in their respective directories. Do not commit either file.

## GET /health

Returns a small liveness response:

```json
{"status": "ok"}
```

## POST /predict

### Request

Send JSON matching [`FlightPredRequest`](../backend/src/models/base_models.py#L48):

```json
{
  "date": "2026-08-20",
  "scheduledDepartureTime": "14:30",
  "depIataCode": "JFK",
  "destIataCode": "LAX"
}
```

The same request can be sent with `curl` while the backend is running:

```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"date":"2026-08-20","scheduledDepartureTime":"14:30","depIataCode":"JFK","destIataCode":"LAX"}'
```

Request rules:

- `date` is an ISO date in `YYYY-MM-DD` form.
- `scheduledDepartureTime` is a time value, normally written as `HH:MM`.
- `depIataCode` and `destIataCode` must each contain exactly three characters. Use uppercase IATA codes because the local airport tables store uppercase codes.
- Unknown request fields are rejected by Pydantic validation.

### Response

Successful responses return [`FlightPredictionResponse`](../backend/src/models/base_models.py#L104) directly. The response is not wrapped in the internal `FuncResponse` object.

```json
{
  "is_significant_delay": false,
  "significant_delay_probability": 0.18,
  "coordinates": {
    "origin_lat": 40.6413,
    "origin_long": -73.7781,
    "dest_lat": 33.9416,
    "dest_long": -118.4085
  },
  "distance": {
    "fl_distance": 2450
  },
  "aviationApiData": {
    "origin": "JFK",
    "origin_city_name": "New York, NY",
    "origin_lat": 40.6413,
    "origin_long": -73.7781,
    "dest": "LAX",
    "dest_city_name": "Los Angeles, CA",
    "dest_lat": 33.9416,
    "dest_long": -118.4085,
    "flight_date": "2026-08-20",
    "day_of_month": 20,
    "day_of_week": 4,
    "pred_dep_time": 1430,
    "pred_arr_time": 1810,
    "pred_elapsed_time": 340,
    "year": 2026,
    "month": 8
  }
}
```

`is_significant_delay` is the classifier output. `significant_delay_probability` is the model's probability for the significant-delay class and is between `0` and `1`; it may be `null` if the loaded model does not provide class probabilities. The target is defined as a delay of at least 25 minutes; see [ML target definition](ml.md#target-definition).

### Failure responses

The service layer uses [`FuncResponse`](../backend/src/models/base_models.py#L53) internally, but the HTTP route does not return that object to clients. [`send_flight_prediction`](../backend/src/main.py#L30) unwraps successful service responses and returns [`FlightPredictionResponse`](../backend/src/models/base_models.py#L104) directly. Failed service responses are converted into `HTTPException`.

Public failure responses therefore use FastAPI's `detail` field, not an `ok: false` wrapper. Project-generated errors usually place a [`PresentError`](../backend/src/models/base_models.py#L5) object inside `detail`:

```json
{
  "detail": {
    "code": 404,
    "description": "Departure airport was not found in weather_req_table.",
    "error": "airport_code=XXX"
  }
}
```

The exact `description` and `error` values vary depending on where the prediction pipeline failed. Request-validation errors use FastAPI's standard validation shape instead.

Common cases include:

| Status | Meaning |
| --- | --- |
| `404` | Airport or scheduled flight could not be found. |
| `422` | The request body failed FastAPI/Pydantic validation. |
| `502` | An external API returned an unusable response. |
| `500` | Local configuration, DuckDB, or model setup failed. |

If AviationStack returns flight data but no item matches the requested route and scheduled departure time, the service returns `404`. If AviationStack or Open-Meteo returns no usable data or an invalid payload, the service generally returns `502`.

Representative examples:

```json
{
  "detail": {
    "code": 404,
    "description": "Departure airport was not found in weather_req_table.",
    "error": "airport_code=XXX"
  }
}
```

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "depIataCode"],
      "msg": "String should have at least 3 characters",
      "input": "JF",
      "ctx": {"min_length": 3}
    }
  ]
}
```

```json
{
  "detail": {
    "code": 502,
    "description": "Aviation API scheduled flight data payload was invalid.",
    "error": "{...provider payload...}"
  }
}
```

```json
{
  "detail": {
    "code": 500,
    "description": "ML model file was not found.",
    "error": "[Errno 2] No such file or directory: '.../model.joblib'"
  }
}
```

The frontend treats any non-2xx response as an error in [`frontend/src/lib/api.ts`](../frontend/src/lib/api.ts).

## External API Dependencies

The prediction workflow uses:

1. [AviationStack](https://docs.apilayer.com/aviationstack/docs/api-documentation), specifically `GET https://api.aviationstack.com/v1/flightsFuture`, to find a scheduled departure for the requested date and origin airport.
2. [Open-Meteo](https://open-meteo.com), specifically `GET https://customer-api.open-meteo.com/v1/forecast`, to retrieve daily weather values for the origin and destination coordinates.

The exact request construction is implemented in [`aviation_api.py`](../backend/src/api/aviation_api.py) and [`weather_api.py`](../backend/src/api/weather_api.py). The service retries selected transient HTTP failures, but external provider availability, coverage, date-range support, and plan limits still affect prediction success and speed. Check the current provider account and pricing pages before assuming a specific supported future-date range.

### External Request Behaviour

External HTTP calls go through [`request_with_retry`](../backend/src/utils.py#L52). Its current defaults are:

| Setting | Value |
| --- | --- |
| Attempts | 3 total attempts |
| Timeout | 25 seconds per request |
| Retryable HTTP statuses | `408`, `429`, `500`, `502`, `503`, `504` |
| Backoff | 3 seconds before the second attempt, then 6 seconds before the third attempt |
| Redirects | Followed by default |

The live `/predict` path requests AviationStack, then origin weather, then destination weather as part of one request flow. It does not currently run those external requests concurrently.

The historical weather-ingestion runner uses [`run_weather_backfill`](../backend/src/ml/weather_api_data_pipeline_funcs.py#L222) with `batch_size=50` and `concurrency=10` from [`weather_api_data_runner.py`](../backend/src/ml/weather_api_data_runner.py).

## Logging

Backend logging is configured by [`configure_logging`](../backend/src/logger_config.py):

| Context | Log file |
| --- | --- |
| API server | `backend/logs/api.log` |
| Weather ingestion | `backend/logs/weather_ingestion.log` |
| Default fallback | `backend/logs/app.log` |

Logs are also written to stdout. File logs use a rotating handler with a 5 MB limit and 3 backups. The `backend/logs` directory is excluded from git.

## Testing

Backend tests are in [`backend/tests/`](../backend/tests/). Run them from the `backend` directory after installing dependencies:

```bash
uv run pytest
```

Relevant API and service coverage includes `test_weather_api.py`, `test_utils.py`, and `test_flight_prediction_service.py`.
