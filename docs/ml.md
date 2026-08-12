# Machine Learning

## Overview

The model predicts whether a flight will have a significant delay. It uses historical flight data, route and schedule features, and daily weather features for the origin and destination airports.

The trained model is loaded by [`predict_delay_from_model`](../backend/services/flight_prediction_sercive.py#L362) during `POST /predict`. The input contract is represented by [`MLModelInput`](../backend/src/models/base_models.py#L114). A pre-trained model is available from [Google Drive](https://drive.google.com/file/d/1KRhr2aaH5HY-2BNteX0C7LtocAqY2zGC/view?usp=sharing). Known model lineage is recorded in [Model Metadata](model-metadata.md).

## Target Definition

The CSV pipeline creates `total_delay` by adding:

- `carrier_delay`
- `weather_delay`
- `nas_delay`
- `security_delay`
- `late_aircraft_delay`

The model dataset exposes this value as `delay`. Training creates the binary target with:

```python
y = (data_df["delay"] >= 25).astype(int)
```

Therefore, class `1` means a delay of at least 25 minutes and class `0` means a delay below 25 minutes. This is a classification target, not an estimate of the exact number of delay minutes.

## Data Sources

### Historical datasets

- [2024 U.S. flight dataset on Kaggle](https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data)
- [U.S. airports dataset from HDX](https://data.humdata.org/dataset/ourairports-usa)

### Runtime and training APIs

- [AviationStack](https://docs.apilayer.com/aviationstack/docs/api-documentation) supplies scheduled flight information at runtime.
- [Open-Meteo](https://open-meteo.com) supplies daily weather data at runtime and during weather ingestion.

## Data Pipeline

The pipeline is:

```text
raw flight CSV + airport CSV
        -> cleaned DuckDB tables
        -> weather request queue
        -> raw weather responses
        -> model_dataset
        -> training and evaluation
        -> model.joblib
```

The main implementation files are:

| Stage | Files | Main output |
| --- | --- | --- |
| Clean source CSVs | [`csv_data_pipeline_funcs.py`](../backend/src/ml/csv_data_pipeline_funcs.py), [`csv_data_pipeline_runner.ipynb`](../backend/src/ml/csv_data_pipeline_runner.ipynb) | `flight_data`, `airport_data`, and `weather_req_table` |
| Fetch and persist weather | [`weather_api_data_runner.py`](../backend/src/ml/weather_api_data_runner.py), [`weather_api_data_pipeline_funcs.py`](../backend/src/ml/weather_api_data_pipeline_funcs.py) | `weather_response_raw` |
| Join features | `create_model_dataset` in [`weather_api_data_pipeline_funcs.py`](../backend/src/ml/weather_api_data_pipeline_funcs.py#L280) | `model_dataset` |
| Train and evaluate | [`train.py`](../backend/src/ml/training/train.py), [`train_optimised.py`](../backend/src/ml/training/train_optimised.py), [`train.ipynb`](../backend/src/ml/training/train.ipynb) | `model.joblib` and training figures/results |

The weather pipeline requests daily values for these fields at both airports: weather code, maximum and minimum temperature, apparent temperature, precipitation, rain, showers, snowfall, cloud cover, wind speed, wind gusts, wind direction, and mean sea-level pressure.

### Schema validation

DuckDB tables are created by SQL in the pipeline functions, not by an ORM or schema-management tool. The expected output shapes for the cleaned CSV tables and weather request table are represented by Pydantic models in [`base_models.py`](../backend/src/models/base_models.py), including `CleanedFlightDuckDBTableCols`, `CleanedAirportDuckDBTableCols`, and `WeatherRequestDuckDBTableCols`.

Those models are used as validation contracts after table creation. They help catch column-name, order, and type drift in tests and pipeline checks, but they do not directly control the DuckDB schema in the way a migration tool or SQLModel table definition would.

## Canonical Local Rebuild Path

The repository does not currently provide one command that downloads data, creates the DuckDB database, fetches weather, trains the model, and verifies every artifact. The canonical local rebuild path is still manual:

> Note that:
> - It is highly recommended that you use the trained model found [here]().
> - If you chose to train your own and explore hyperparameter tuning(s), it will take hours, and maybe over a day, depending on your computer's specs. During which you will be unable to sue your computer to its intended ability. This is why it is recommended to use a remote instance. I used AWS's EC2, and used scp to copy results back to my computer.

1. Download the source datasets listed in [Data Sources](#data-sources).
2. Place the raw CSV files at:

   ```text
   backend/data/csv/flight_data_2024.csv
   backend/data/csv/us-airports.csv
   ```

3. Run [`csv_data_pipeline_runner.ipynb`](../backend/src/ml/csv_data_pipeline_runner.ipynb). It is configured to create `backend/data/duck_database.duckdb` and populate:

   - `flight_data`
   - `airport_data`
   - `weather_req_table`

4. From the repository root, run the weather ingestion and model-dataset build:

   ```bash
   cd backend
   uv run python src/ml/weather_api_data_runner.py
   ```

   This reads `weather_req_table`, writes raw Open-Meteo responses to `weather_response_raw`, and then creates `model_dataset`. It can take a long time because it performs many external API requests.

5. Train the selected model:

   ```bash
   cd backend
   uv run python src/ml/training/train_optimised.py
   ```

   This reads `model_dataset` and writes `backend/src/ml/model/model.joblib`. Use [`train.py`](../backend/src/ml/training/train.py) instead when you want to rerun the exploratory randomized-search workflow and regenerate evaluation figures.

For a working prediction environment, these generated artifacts must exist:

```text
backend/data/duck_database.duckdb
backend/src/ml/model/model.joblib
```

The database should contain at least these tables:

```sql
SHOW TABLES;
SELECT COUNT(*) FROM flight_data;
SELECT COUNT(*) FROM airport_data;
SELECT COUNT(*) FROM weather_req_table;
SELECT COUNT(*) FROM weather_response_raw;
SELECT COUNT(*) FROM model_dataset;
```

`/predict` only requires `airport_data`, `weather_req_table`, and `model.joblib` at runtime, but the saved model is only reproducible from the same `model_dataset` shape used by training. If you replace the database or rebuild `model_dataset`, retrain `model.joblib` before trusting the reported metrics.

## Model Features

The classifier uses:

- Schedule and route values: year, month, day of month, day of week, scheduled departure and arrival times, elapsed time, and route distance.
- Origin weather values: daily weather code, temperatures, apparent temperatures, precipitation, rain, showers, snowfall, cloud cover, wind speed, wind gusts, wind direction, and pressure.
- Destination weather values: the same daily weather fields as the origin.
- Categorical values: flight date, origin IATA code, and destination IATA code.

The training pipeline one-hot encodes the categorical values and passes the numeric values through unchanged. The inference path builds the same feature names before calling the saved pipeline.

## Local Artifacts

Generated data and model files are excluded from git by [`.gitignore`](../.gitignore). A working prediction environment needs:

- `backend/data/duck_database.duckdb`, with `airport_data` and `weather_req_table` available to the prediction service.
- `backend/src/ml/model/model.joblib`, containing the fitted scikit-learn pipeline.

See [Model Metadata](model-metadata.md) for the source inputs, generated artifacts, model contract, evaluation summary, and backend package constraints associated with the documented model.

To rebuild the data artifacts, obtain the source CSVs, run the CSV pipeline notebook or its functions to create `flight_data` and `airport_data`, run the weather ingestion runner, and let it create `model_dataset`. To train a replacement model, run `train.py` for the exploratory and randomized-search workflow or `train_optimised.py` with the selected parameters. These workflows make many API requests and can take a long time.

## Training and Evaluation

The final training script, [`train_optimised.py`](../backend/src/ml/training/train_optimised.py), reads from `model_dataset` with:

```sql
SELECT * FROM model_dataset LIMIT 1000000
```

It then drops rows containing nulls before building the feature matrix and target. The exact number of rows remaining after `dropna`, the train/test row counts, and the positive/negative class counts were printed or implied during training but are not currently persisted in a checked-in summary file.

The training scripts use a stratified random 80/20 train/test split with `random_state=1`; this is not a time-based split. `train.py` uses `RandomizedSearchCV` with three cross-validation folds and optimises F1. `train_optimised.py` uses the selected random forest parameters to create the saved model.

The dummy-baseline comparison in `train.py` evaluates `DummyClassifier` with `most_frequent`, `stratified`, and `uniform` strategies. The exact baseline scores are only stored in the generated `dummy_strats.png` figure, not in a machine-readable results file.

The checked-in results file is [`best_results.txt`](../backend/src/ml/training/figures/train_results/best_results.txt). The figures are in [`backend/src/ml/training/figures/`](../backend/src/ml/training/figures/):

- `correlation_chart.png`
- `delay_distribution.png`
- `missing_values.png`
- `dummy_strats.png`

The recorded evaluation values are:

| Metric | Value |
| --- | ---: |
| Accuracy | 0.780 |
| Precision | 0.420 |
| Recall | 0.528 |
| F1 | 0.468 |
| ROC AUC | 0.758 |
| Cross-validation F1 | 0.461 |

These numbers describe the saved experiment, not a guarantee of future prediction quality. The `DummyClassifier` baseline also shows why accuracy alone is not sufficient for this imbalanced target.

## Testing

Backend tests are in [`backend/tests/`](../backend/tests/). Run them from `backend` with:

```bash
uv run pytest
```

The tests cover model validation, pipeline schema checks, utility functions, external API helpers, and the prediction service.

## Limitations

- The historical data is from 2024 and may not represent later flight operations.
- Weather is represented by daily summaries, not conditions at the exact scheduled departure or arrival time.
- The feature set lacks operational and historical context such as aircraft rotation, gate activity, staffing, and route-level delay history.
- The target combines several delay categories into one total and then discards the exact delay duration by thresholding it.
- API coverage and plan limits can make data ingestion incomplete.
- The training and ingestion workflows are expensive in time and external API calls.

## Future Work

- Generate model metadata automatically when training writes a new artifact.
- Add an automated data-preparation command if the manual rebuild path becomes too error-prone.
- Compare the current model with time-based validation and stronger baselines.
- Test alternative weather windows and operational features.
- Consider a different live flight-data provider if AviationStack coverage or latency remains a problem.

Track broader project tasks in the [GitHub issues](https://github.com/magnusrwn/flight_proj/issues).
