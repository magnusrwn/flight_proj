# Architecture

## Purpose

This repository is a small full-stack machine-learning application. The frontend collects a flight lookup, the FastAPI backend assembles live and local data, and a scikit-learn classifier predicts whether the flight will be significantly delayed.

The project is primarily a learning and portfolio exercise. It is designed to run locally, which explains the deliberately small operational surface: there is no user account system, application-level rate limiting, deployment configuration, Docker setup, or production hosting workflow.

## Scope and Boundaries

### In scope

- A React and TypeScript interface for one prediction workflow
- A FastAPI backend with `GET /health` and `POST /predict`
- Local DuckDB data access
- AviationStack and Open-Meteo integrations
- A pre-trained random forest classifier and the scripts used to train it
- Unit and integration tests for backend logic

### Out of scope for this iteration

- Authentication and user accounts
- Application-level rate limiting
- Hosting, deployment, and infrastructure configuration
- Docker or container orchestration
- Background job management for the live prediction endpoint

These are boundaries, not missing setup instructions. The current project goal is local execution and learning.

## Components

| Component | Responsibility | Main location |
| --- | --- | --- |
| Frontend | Collects and validates input, calls the backend, and renders prediction or error state. | [`frontend/src/App.tsx`](../frontend/src/App.tsx) |
| API application | Defines routes, CORS, validation, and HTTP error translation. | [`backend/src/main.py`](../backend/src/main.py) |
| Prediction service | Coordinates local lookup, external requests, feature construction, and model inference. | [`flight_prediction_sercive.py`](../backend/services/flight_prediction_sercive.py) |
| External API clients | Builds requests for AviationStack and Open-Meteo. | [`backend/src/api/`](../backend/src/api/) |
| Data layer | Stores airport, flight, weather, and model-ready tables in DuckDB. | [`backend/src/ml/`](../backend/src/ml/) |
| Base Models | Defines request, response, and internal data models with Pydantic. | [`base_models.py`](../backend/src/models/base_models.py) |

## Runtime Flow

For a successful `POST /predict` request:

1. FastAPI validates the request against `FlightPredRequest`.
2. The service checks that the departure airport exists in the local `weather_req_table`.
3. AviationStack is queried for future departures on the requested date and origin airport.
4. The matching route and scheduled time are selected from the AviationStack response.
5. The service joins the route to airport coordinates in the local `airport_data` table and derives date/time features.
6. The route distance is calculated from the two coordinate pairs.
7. Open-Meteo is queried for daily weather at the origin and destination.
8. Weather and flight values are validated and assembled into the model feature contract.
9. `model.joblib` predicts the binary delay class and, when supported, its probability.
10. FastAPI returns the prediction and selected flight metadata.

The public request and response contract is documented in the [API reference](api.md#post-predict).

## Data and Storage

DuckDB is used as a local file database at `backend/data/duck_database.duckdb`. It avoids loading large CSV files into memory during every operation and keeps the project self-contained.

The pipeline creates or uses these important tables:

- `flight_data`: cleaned historical flights and the component delay columns combined into `total_delay`.
- `airport_data`: airport names, coordinates, and IATA codes.
- `weather_req_table`: one weather request row per airport/date, with processing status.
- `weather_response_raw`: raw weather responses keyed by airport and date.
- `model_dataset`: historical flight rows joined with origin and destination weather features.

The database is a generated local artifact and is excluded from git. See [ML local artifacts](ml.md#local-artifacts) for the pipeline that creates it.

## Frontend Architecture

The frontend is intentionally thin:

- [`FlightLookupForm.tsx`](../frontend/src/features/flight-lookup/FlightLookupForm.tsx) collects and validates form input.
- [`frontend/src/lib/api.ts`](../frontend/src/lib/api.ts) makes the single `POST /predict` request.
- [`PredictionResult.tsx`](../frontend/src/features/prediction-result/PredictionResult.tsx) renders success and error states.
- [`frontend/src/types/api.ts`](../frontend/src/types/api.ts) contains the TypeScript request and response contracts.
- [`App.tsx`](../frontend/src/App.tsx) owns request state and composes the page.

## Backend Architecture

The backend separates route handling from the prediction workflow. Pydantic models validate boundaries, API modules handle external requests, utility functions handle shared operations, and the service coordinates the end-to-end process. The model is loaded from `backend/src/ml/model/model.joblib` when a prediction is made.

## Routes, Errors, and CORS

The route list and exact response contract are maintained in the [API reference](api.md). In summary:

- `/health` returns `{"status": "ok"}` when the application is running.
- `/predict` returns `FlightPredictionResponse` directly on success.
- `/predict` raises HTTP errors for invalid input, missing data, external API failures, and model or local configuration failures.
- CORS allows the Vite development origin `http://localhost:5173` in [`main.py`](../backend/src/main.py#L17).

Internal service functions use `FuncResponse` to carry success, code, message, and data between layers. The public route translates failed service responses into HTTP exceptions rather than exposing that internal wrapper on successful responses.

## Logging

Logging is configured in [`logger_config.py`](../backend/src/logger_config.py). API logs are written to `backend/logs/api.log`; the weather ingestion runner writes to `backend/logs/weather_ingestion.log`. The logs directory is local and excluded from git.

## Performance

Live predictions depend on at least one AviationStack request and two Open-Meteo requests, so network latency dominates the request time. The training and weather-ingestion pipelines can process large datasets and are more suitable for a machine with sufficient memory and CPU than for a small laptop. The project used an EC2 machine for long-running training and ingestion jobs, but no hosting setup is part of this repository.

## Known Limitations

- AviationStack coverage and future-date availability are outside this project's control, and some popular flights may not be returned.
- The prediction uses daily weather summaries rather than weather at the scheduled departure or arrival time.
- The feature set does not include operational context such as previous flights on the same aircraft, gate congestion, crew availability, or route history.
- The model was trained on 2024 U.S. flight data, so performance may not transfer to later periods or other markets.
- The local database and model artifact must be prepared separately because generated data and `*.joblib` files are ignored by git.

The [ML documentation](ml.md#limitations) contains the modelling-specific limitations and future work.
