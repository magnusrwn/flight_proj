# Documentation
> 🚧 Under construction 🚧

## API's used
- Open-meteo historical weather api: https://open-meteo.com/
## External data sources
- Flight data source (untracked in this repo): https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data

## Backend
- FastAPI PostgreSQL

## Frontend
- `frontend/` contains a single-page `Vite + React + TypeScript` app scaffold.
- It currently expects a backend prediction endpoint at `POST /predict`.
- Set frontend env vars in `frontend/.env` if needed:
  - `VITE_API_BASE_URL=http://localhost:8000`
  - `VITE_PREDICTION_ENDPOINT=/predict`
- Planned map direction for later integration: `react-leaflet` with OpenStreetMap tiles.

## Other services
- Docker
- AWS for hosting and compute