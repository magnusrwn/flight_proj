# Model Metadata

This file records the known lineage for the checked documentation and downloadable model artifact. It intentionally avoids fields that are not currently useful or reliably recorded, such as raw row counts and dataset download dates.

## Source Inputs

| Input | Source | Expected local path |
| --- | --- | --- |
| Historical U.S. flight CSV | [2024 U.S. flight dataset on Kaggle](https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data) | `backend/data/csv/flight_data_2024.csv` |
| U.S. airports CSV | [U.S. airports dataset from HDX](https://data.humdata.org/dataset/ourairports-usa) | `backend/data/csv/us-airports.csv` |
| Daily weather | [Open-Meteo](https://open-meteo.com) | Persisted into `weather_response_raw` |

## Generated Artifacts

| Artifact | Path or table | Produced by |
| --- | --- | --- |
| Local DuckDB database | `backend/data/duck_database.duckdb` | [`csv_data_pipeline_runner.ipynb`](../backend/src/ml/csv_data_pipeline_runner.ipynb), then [`weather_api_data_runner.py`](../backend/src/ml/weather_api_data_runner.py) |
| Cleaned flights | `flight_data` | [`create_and_clean_flights_table`](../backend/src/ml/csv_data_pipeline_funcs.py) |
| Cleaned airports | `airport_data` | [`create_and_clean_airport_table`](../backend/src/ml/csv_data_pipeline_funcs.py) |
| Weather request queue | `weather_req_table` | [`create_weather_req_table`](../backend/src/ml/csv_data_pipeline_funcs.py) |
| Raw weather responses | `weather_response_raw` | [`run_weather_backfill`](../backend/src/ml/weather_api_data_pipeline_funcs.py) |
| Model-ready joined table | `model_dataset` | [`create_model_dataset`](../backend/src/ml/weather_api_data_pipeline_funcs.py#L280) |
| Saved model | `backend/src/ml/model/model.joblib` | [`train_optimised.py`](../backend/src/ml/training/train_optimised.py) |

## Model Contract

| Field | Value |
| --- | --- |
| Model type | scikit-learn `Pipeline` with `ColumnTransformer`, `OneHotEncoder`, and `RandomForestClassifier` |
| Target | Binary classification: `delay >= 25` minutes |
| Positive class | Significant delay, at least 25 minutes |
| Training row query | `SELECT * FROM model_dataset LIMIT 1000000` |
| Null handling | Rows containing nulls are dropped before splitting |
| Split | Stratified random 80/20 split with `random_state=1` |
| Time-based validation | Not used for the recorded model |
| Training source | `model_dataset` in `backend/data/duck_database.duckdb` |
| Runtime model path | `backend/src/ml/model/model.joblib` |
| Runtime input model | [`MLModelInput`](../backend/src/models/base_models.py#L114) |
| Runtime prediction function | [`predict_delay_from_model`](../backend/services/flight_prediction_service.py#L362) |

The feature list is documented in [Model Features](ml.md#model-features). The canonical local rebuild sequence is documented in [Canonical Local Rebuild Path](ml.md#canonical-local-rebuild-path).

## Recorded Evaluation

The current documentation records the selected run from [`best_results.txt`](../backend/src/ml/training/figures/train_results/best_results.txt):

| Metric | Value |
| --- | ---: |
| Accuracy | 0.780 |
| Precision | 0.420 |
| Recall | 0.528 |
| F1 | 0.468 |
| ROC AUC | 0.758 |
| Cross-validation F1 | 0.461 |

These values describe the recorded experiment, not a guarantee for later data or rebuilt artifacts.

The exact post-cleaning row count, train/test row counts, class counts, and dummy-baseline scores are not currently persisted in a checked-in summary file.

## Backend Environment

The backend package constraints are declared in [`backend/pyproject.toml`](../backend/pyproject.toml):

| Package | Constraint |
| --- | --- |
| Python | `>=3.13` |
| duckdb | `>=1.5.5` |
| fastapi | `>=0.139.0` |
| httpx | `>=0.28.1` |
| joblib | `>=1.5.3` |
| pandas | `>=3.0.3` |
| pydantic | `>=2.13.4` |
| scikit-learn | `>=1.9.0` |
| uvicorn | `>=0.51.0` |

Use `backend/uv.lock` for the exact locked dependency resolution used by `uv`.
