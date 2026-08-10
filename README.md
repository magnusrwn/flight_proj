# Welcome to My Flight Delay Predictor

Predict whether a US flight  is likely to be notably delayed
historical flight and weather data.

[SCREENSHOT/ GIF OF APPLICATION, UPLOAD THIS LATER]

## Overview
Certain flights have greater chances of being delayed. This is due to factors such as airline, staffing, weather time of year, etc...

And so, I thought it would be an interesting process to try and use (nearly) free data that is possible to obtain on the internet in order to predict real flights with a hometrained ML model.

---

## Features
- Flight delay prediction through random forest classification with estimated confidence/probability
- Weather integration through Open-Meteo's API. Link [here](https://open-meteo.com)
- Interactive flight input
- Flight data integration using AviationStack API. Link [here](https://docs.apilayer.com/aviationstack/docs/api-documentation)

---

## Tech Stack With Links

**Frontend**
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vite.dev/)

**Backend**
- [Python](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)

**ML / Data**
- [pandas](https://pandas.pydata.org/docs/)
- [scikit-learn](https://scikit-learn.org/stable/)
- [DuckDB](https://duckdb.org/docs/current/)
    - Highly recommended
- [Open-Meteo API](https://open-meteo.com)
- [AviationStack API](https://docs.apilayer.com/aviationstack/docs/api-documentation)
- [Internal flights in the USA in 2024](https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data)
- [Matplotlib](https://matplotlib.org/3.5.3/index.html)

---

## Machine Learning

### Rough flow:
- Hard input vars: airport_data, 2024_flight_data
    - Process through data pipelines
- Query to weather API
- Put response through pipeline
- Explore data
- Train model

>For ML docs look [here](https://github.com/magnusrwn/flight_proj/blob/main/docs/ml.md)

---

## Running Locally

### Pre-reqs:
- Ensure Python is installed on your computer
- Ensure uv is installed on your computer

### Backend Steps:
- Open a new terminal
- `cd /backend`
- `uv run uvicorn src.main:app --reload`

### Frontend
- Open a new terminal
- `cd frontend`
- `npm init -y`
- `npm i`
- `npm run dev`

### .env Configuration
See @`backend/.env.example` and @`frontend/.env.example` for vars
- Place your frontend `.env` at `/frontend/.env`
- Place your backend `.env` at `/backend/.env`

---

## API
Endpoint name: `POST /predict`

Note, being the only backend API communication this is already configured in the .env.example, so simply leave it there/ move the copy to your `frontend/.env`

**Request shape:**
``` text
{
  date: string;
  scheduledDepartureTime: string;
  depIataCode: string;
  destIataCode: string;
}
```

**Response shape:**

``` text
{
    ok:boolean;
    code: int | null;
    message: string;
    data:{
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
    }
}
```
>See API documentation [here](https://github.com/magnusrwn/flight_proj/blob/main/docs/api.md)
## Project Structure
```text
.
|-- backend/                 # Python API, ML pipeline, models, services, and tests
|   |-- pyproject.toml       # Backend dependencies and project config
|   |-- uv.lock              # Locked backend dependency versions
|   |-- .env.example         # Example backend environment variables
|   |-- services/            # Service layer for prediction workflows
|   |-- src/
|   |   |-- main.py          # Backend application entry point
|   |   |-- api/             # External API integrations
|   |   |-- ml/              # Data pipelines, training code, notebooks, and model helpers
|   |   `-- models/          # Shared data models
|   `-- tests/               # Backend unit and integration tests
|-- frontend/                # Vite, React, and TypeScript frontend
|   |-- package.json         # Frontend scripts and dependencies
|   |-- vite.config.ts       # Vite configuration
|   |-- .env.example         # Example frontend environment variables
|   `-- src/
|       |-- components/      # Shared UI components
|       |-- features/        # Feature-specific frontend modules
|       |-- lib/             # Frontend API/client helpers
|       `-- types/           # Shared TypeScript types
|-- docs/                    # Extended project documentation
|   |-- api.md
|   |-- architecture.md
|   `-- ml.md
|-- README.md
`-- newREADMEtemplate.md
```

Local/generated files are omitted from this tree, including `.env` files, `backend/data/`, `backend/logs/`, virtual environments, `node_modules/`, frontend build output, caches, and trained model artifacts.

---

## Further Documentation Links

- Architecture [here](https://github.com/magnusrwn/flight_proj/blob/main/docs/architecture.md)
- ML pipeline [here](https://github.com/magnusrwn/flight_proj/blob/main/docs/ml.md)
- API link [here](https://github.com/magnusrwn/flight_proj/blob/main/docs/api.md)

---

## Future Work For This Project
Find the future plans/ work/ todos for this project [here](https://github.com/magnusrwn/flight_proj/issues) 
