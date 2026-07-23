# 🚧 Under construction 🚧

# Note that ⚠️
All code in this repo is reviewed line by line to ensure I understand it, and the vast majority is written by hand. This is mainly a refresh/ improve task however, also for learning (with thing such as ML, testing, pyplot), of course. So, code will take time, and is likely hand written, or prompted and then significantly chopped down. This may also lead to code-comments of explanations of different things.

## API's used
- Open-meteo historical weather api: https://open-meteo.com/
## External data sources
- Flight data source (untracked in this repo): https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data

## Frontend scaffold
- `frontend/` contains a single-page `Vite + React + TypeScript` app scaffold.
- It currently expects a backend prediction endpoint at `POST /predict`.
- Set frontend env vars in `frontend/.env` if needed:
  - `VITE_API_BASE_URL=http://localhost:8000`
  - `VITE_PREDICTION_ENDPOINT=/predict`
- Planned map direction for later integration: `react-leaflet` with OpenStreetMap tiles.
