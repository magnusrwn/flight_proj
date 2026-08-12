# Flight Delay Predictor

This project predicts whether a domestic U.S. flight is likely to have a significant delay. It combines 2024 historical flight data with daily weather data, a local DuckDB database, live flight schedule data, and a scikit-learn random forest classifier.

It is a local portfolio and learning project. Its purpose is to practise typed full-stack development, data pipelines, API integration, testing, and machine learning. It is not designed as a production service.

## Documentation

- [Run the project locally](#running-locally)
- [API reference](docs/api.md)
- [System architecture](docs/architecture.md)
- [ML pipeline and evaluation](docs/ml.md)
- [Documentation recommendations](docs/recommendations.md)

## What It Does

The frontend accepts:

- A flight date
- A scheduled departure time
- A three-letter departure airport IATA code
- A three-letter destination airport IATA code

The backend then checks the local airport data, requests the scheduled flight from AviationStack, requests daily weather data from Open-Meteo for both airports, calculates the route distance, and sends the resulting features to the trained model. The response contains a significant-delay prediction, its model probability when available, and selected flight details.

The model defines a significant delay as at least 25 minutes. See [the ML documentation](docs/ml.md#target-definition) for the label definition and evaluation context.

## Features

- Random forest classification with a significant-delay probability
- Live scheduled-flight lookup through [AviationStack](https://docs.apilayer.com/aviationstack/docs/api-documentation)
- Daily airport weather lookup through [Open-Meteo](https://open-meteo.com)
- Local DuckDB storage for airport, flight, weather, and training data
- React and TypeScript frontend with a single prediction workflow

## Technology

- Frontend: [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vite.dev/), and [Tailwind CSS](https://tailwindcss.com/)
- Backend: [Python](https://www.python.org/), [FastAPI](https://fastapi.tiangolo.com/), and [uvicorn](https://www.uvicorn.org/)
- Data and ML: [DuckDB](https://duckdb.org/), [pandas](https://pandas.pydata.org/docs/), [scikit-learn](https://scikit-learn.org/stable/), and [Matplotlib](https://matplotlib.org/)

## Running Locally

### Prerequisites

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- API keys for AviationStack and Open-Meteo

### 1. Prepare the backend

From the project root:

```bash
cp backend/.env.example backend/.env
cd backend
uv sync
```

Set the values in `backend/.env` as described in [Environment Variables](docs/api.md#environment-variables).

The backend expects these local artifacts, which are excluded from git:

- `backend/data/duck_database.duckdb`, containing at least the `airport_data` and `weather_req_table` tables for predictions
- `backend/src/ml/model/model.joblib`, the trained model used by `/predict`

The [ML documentation](docs/ml.md#local-artifacts) explains how the data pipeline and model fit together. A pre-trained model is available from [Google Drive](https://drive.google.com/file/d/1KRhr2aaH5HY-2BNteX0C7LtocAqY2zGC/view?usp=sharing); place it at `backend/src/ml/model/model.joblib`.

Start the API from the `backend` directory:

```bash
uv run uvicorn src.main:app --reload
```

The backend runs at `http://localhost:8000`.

### 2. Prepare the frontend

In a second terminal, from the project root:

```bash
cp frontend/.env.example frontend/.env
cd frontend
npm install
npm run dev
```

The Vite development server runs at `http://localhost:5173` by default. The frontend variables are documented in [Environment Variables](docs/api.md#environment-variables).

### 3. Try the API

Check that the backend is running:

```bash
curl http://localhost:8000/health
```

For the request contract, response fields, and failure behaviour, see the [API reference](docs/api.md).

## Project Structure

```text
.
|-- backend/
|   |-- pyproject.toml       # Backend dependencies and project configuration
|   |-- .env.example         # Backend environment variable template
|   |-- services/            # Prediction workflow
|   |-- src/
|   |   |-- main.py          # FastAPI application and routes
|   |   |-- api/             # External API clients
|   |   |-- ml/              # Data pipelines and training code
|   |   |-- models/          # Pydantic contracts
|   |   `-- utils.py         # Shared backend helpers
|   `-- tests/               # Backend tests
|-- frontend/
|   |-- package.json         # Frontend scripts and dependencies
|   |-- .env.example         # Frontend environment variable template
|   `-- src/
|       |-- components/      # Shared UI components
|       |-- features/        # Feature-specific UI modules
|       |-- lib/             # Frontend API client
|       `-- types/           # TypeScript API contracts
|-- docs/
|   |-- api.md
|   |-- architecture.md
|   |-- ml.md
|   `-- recommendations.md
`-- README.md
```

Generated and local-only files are omitted from this tree, including `.env` files, `backend/data/`, `backend/logs/`, virtual environments, `node_modules/`, build output, caches, and the trained model artifact.

## Scope and Limitations

The project is intended for local use. It does not currently include user authentication, application-level rate limiting, deployment or hosting configuration, Docker configuration, or production operations. CORS is configured only for the local Vite origin. These boundaries are intentional for the current project goal; see [Architecture](docs/architecture.md#scope-and-boundaries).

The live prediction path can be slow because it depends on external API response times. AviationStack may not provide every flight or every future date. The model is also limited by the quality and depth of its historical and daily weather features. See [Known Limitations](docs/architecture.md#known-limitations) and [ML Limitations](docs/ml.md#limitations).

## Future Work

Track project-level ideas in the [GitHub issues](https://github.com/magnusrwn/flight_proj/issues).
