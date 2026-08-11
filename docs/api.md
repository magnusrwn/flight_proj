# API

Use this file as a guided draft. Answer the questions under each heading, then replace the prompts with final API documentation. For endpoint sections, aim to include exact request/response JSON examples once the answers are known.

## Overview

- What does this API allow a client to do?
- Which clients currently use it?
- Is this API public, local-only, or intended for a portfolio/demo?
- What backend framework serves the API?
- What are the current endpoints?

## Base URL

- What is the local development base URL?
- What base URL should the frontend use by default?
- Is there a deployed base URL?
- How should the base URL be configured in different environments?

## Environment Variables

- Which backend environment variables are required?
- Which frontend environment variables control API calls?
- What are the default values if frontend env vars are missing?
- Where should `.env` files live?
- Which variables are secrets and must not be committed?

## Authentication

- Does your own API require authentication?
- Do any endpoints require user identity?
- Which external APIs require API keys?
- Where are external API keys loaded from?
- What authentication or rate-limit concerns would matter in production?

## Request Format

- What content type should clients send?
- Are all requests JSON?
- What date and time formats are expected?
- Are IATA airport codes case-sensitive?
- Are unknown or extra request fields accepted?
- What validation does Pydantic enforce?

## Response Format

- What content type does the API return?
- Does a successful prediction return the response object directly or inside an envelope?
- Which fields are booleans, numbers, strings, objects, or nullable?
- Which date fields are serialized as strings?
- Which response fields come from AviationStack, DuckDB, distance calculation, and the ML model?

## Response Envelope

- Does the public API return the internal `FuncResponse` envelope?
- Where is `FuncResponse` used internally?
- Should future endpoints return a consistent envelope such as `{ ok, code, message, data }`?
- If the README mentions an envelope, does it match the actual FastAPI response?
- What response shape should clients rely on today?

## Error Handling

- What shape does FastAPI return for `HTTPException` errors?
- What is included in the `detail` field?
- Which failures return `400`, `404`, `422`, `500`, or `502`?
- How are service-layer errors converted into HTTP errors?
- How does the frontend currently display or handle failed requests?
- Are external API errors exposed directly or normalized?

## Validation Rules

- Which fields are required in `FlightPredRequest`?
- What type and format must `date` use?
- What type and format must `scheduledDepartureTime` use?
- What length must `depIataCode` and `destIataCode` have?
- Are extra fields forbidden?
- Are airport codes checked against local DuckDB data?
- Are coordinates validated before distance calculation?

## Endpoints

- Which endpoints exist today?
- Which endpoints are intended for users versus health checks or internal diagnostics?
- Are there endpoints that are planned but not implemented?
- Which endpoint does the frontend call?

### GET /health

#### Purpose

- What is this endpoint used for?
- Should it be used by developers, deployment health checks, or both?
- Does it verify only that FastAPI is running, or also dependencies like DuckDB, model artifact, and external APIs?

#### Success Response

- What JSON is returned when the API is healthy?
- What status code is returned?
- Should this response include version or dependency status in the future?

### POST /predict

#### Purpose

- What user action triggers this endpoint?
- What prediction does it produce?
- What external dependencies are involved?
- What local artifacts must exist for it to work?

#### Request Body

- What is the exact JSON schema?
- Which fields are required?
- What example request should be shown?
- What are valid examples of `date` and `scheduledDepartureTime`?
- Should airport codes be documented as IATA codes?
- Should clients uppercase airport codes before sending?

#### Success Response

- What is the exact JSON schema for a successful response?
- What does `is_significant_delay` mean?
- What does `significant_delay_probability` represent?
- When can `significant_delay_probability` be `null`?
- What is included in `coordinates`?
- What is included in `distance`?
- What is included in `aviationApiData`?
- What example response should be shown?

#### Error Responses

- What happens when the request body fails Pydantic validation?
- What happens when the departure airport is not in `weather_req_table`?
- What happens when AviationStack returns no usable flight data?
- What happens when no AviationStack flight matches the requested route and time?
- What happens when Open-Meteo fails or returns incomplete weather data?
- What happens when DuckDB tables or the model artifact are missing?
- What example error responses should be shown?

#### Example Request

- What is a realistic request payload that works locally?
- Does the example use a real flight date, departure time, origin, and destination?
- Does the example avoid exposing API keys or private data?

#### Example Response

- What is a realistic successful response?
- Are numbers and dates formatted exactly as FastAPI returns them?
- Does the example make clear that probabilities are between `0` and `1`?
- Should the example include both the prediction and supporting flight details?

## External API Dependencies

- Which external APIs are called during prediction?
- Which external APIs are called only during offline data preparation?
- What API keys are needed?
- What rate limits, costs, or availability risks exist?
- What happens if external API response shapes change?

### AviationStack

- Which endpoint is called?
- What parameters are sent?
- What fields are read from the response?
- How is a matching flight selected?
- What assumptions are made about scheduled departure and arrival time fields?
- What errors should be documented for missing API key, empty response, or changed payload shape?

### Open-Meteo

- Which endpoint is called at request time?
- Which endpoint is used for historical training backfill?
- What parameters are sent?
- Which daily weather fields are requested?
- Are requests made for both origin and destination?
- What errors should be documented for missing API key, invalid payload, or failed fetch?

## Frontend API Client

- Where is the frontend API client implemented?
- Which function calls `POST /predict`?
- Which TypeScript types describe request and response data?
- How does the frontend configure `VITE_API_BASE_URL` and `VITE_PREDICTION_ENDPOINT`?
- How are non-OK HTTP responses converted into frontend errors?
- Does the frontend need to handle backend validation errors differently?

## Testing

- Which backend tests cover API models, service behavior, and external API wrappers?
- Is `GET /health` tested?
- Is `POST /predict` tested with success and failure cases?
- Are external APIs mocked in tests?
- Are frontend API client tests needed?
- What manual curl or HTTPie commands should be included for local verification?

## Troubleshooting

- What should a developer check if the frontend cannot reach the backend?
- What should they check if CORS fails?
- What should they check if `POST /predict` returns `422`?
- What should they check if the response is `404`?
- What should they check if the response is `500` or `502`?
- How can they confirm API keys, DuckDB tables, and model artifacts are present?

## Future API Work

- Should the API add versioning, such as `/v1/predict`?
- Should errors use a documented response schema?
- Should there be endpoints for airport search, supported routes, model metadata, or prediction history?
- Should the API cache external API responses?
- Should authentication or rate limiting be added before deployment?
- Should the frontend and backend share generated types from OpenAPI?
