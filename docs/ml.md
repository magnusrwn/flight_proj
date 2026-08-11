# Machine Learning
⚠️ delete this top-doc line summary after, of course...
Use this file as a guided draft. Answer the questions under each heading, then replace the prompts with your final explanation. It is fine to start with short bullet answers.

---

## Overview

- This model takes in the weather and flight data, and outputs a prediction on the flight being significantly delayed (>25min), or not.
- The Model is used within the `flight_prediction_sercive.py` file which holds the main function/ logic for the endpoint `/predict`
- The model is downloadable in the g-drive link, located [here](https://drive.google.com/file/d/1KRhr2aaH5HY-2BNteX0C7LtocAqY2zGC/view?usp=sharing)
- To see input, see `MLModelInput` in file `backend/src/models/base_models.py`

---

## Model setup:
- Download my ML Model from Google drive [here](https://drive.google.com/file/d/1KRhr2aaH5HY-2BNteX0C7LtocAqY2zGC/view?usp=sharing)
- Open a new terminal and cd to the project root
- Run the command `mv [PATH-TO-DOWNLOADED-MODEL].joblib backend/src/ml/model/model.joblib`

---

## Problem Definition
For predicting an exact delay, regression would usually be the prefered way. However, that being said, after training and tring to tune regressive random forests I discorvered it's quite hard to get notably better than taking hte average of the training data.

Thus, I thoguht that making hte delay a binary would be beneficial for the training results, allowing for a higher probability of actual utility. This change can be seen clearly in `/backend/src/ml/train/train.ipynb`.

The model preformed better than taking the avg when the Y was turned into a binary and the model switched to a classifier however, still has room for improvement.

---

## Success Metrics

> NOTE: start ec2 and see logs for this
- Which metrics do you use to judge the model?
- Why are accuracy, precision, recall, F1, and ROC AUC useful or limited here?
- Which metric matters most for this project, and why?
- What baseline should the trained model beat?
- What score would be good enough for a demo or portfolio project?
- How should class imbalance affect metric choice?

---

## Data Cleaning
> Explain the data clean process
- What cleaning steps happen before model training?
- Which rows are removed and why?
- Which columns are cast to new types?
- How are missing delay values handled?
- How are schema mismatches detected?
- What data cleaning choices could bias the model?

---

## Data Sources
**APIs Used:**
- [Open-Meteo API](https://open-meteo.com) for all weather data. *Rate limits
- [Aviation Stack API](https://docs.apilayer.com/aviationstack/docs/api-documentation) for future flight schedule information. * Strong rate limits

**Datasets Used**
- Kaggle [2024 USA flighs](https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data) convering each flight in the USA during the year 2024.
- [Americaon airports dataset](https://data.humdata.org/dataset/ourairports-usa) from the HDX (UN data project) showing each airport in the USA.

---

## Data Schema

Descriptions of important datasets throughout the project
> Note: these are cols after being run throguh `csv_data_pipeline_runner.ipynb`

### Raw Flight Columns
| Column            | Type    |
|-------------------|---------|
| date              | date    |
| year              | integer |
| month             | integer |
| day_of_month      | integer |
| day_of_week       | integer |
| flight_number     | double  |
| origin            | varchar |
| origin_city_name  | varchar |
| dest              | varchar |
| dest_city_name    | varchar |
| pred_dep_time     | bigint  |
| pred_arr_time     | bigint  |
| pred_elapsed_time | double  |
| distance          | double  |
| total_delay       | double  |


### Raw Airport Columns

| Column | Type    |
|--------|---------|
| name   | varchar |
| lat    | double  |
| long   | double  |
| code   | varchar |

### Weather Features

|Column      |Type       |
|------------|-----------|
| code       | varchar   |
| date       | date      |
| api_url    | varchar   |
| fetched_at | timestamp |
| payload    | json      |

|
|
 -- >
 ```
 payload = {                                                                                    
   "latitude": "DOUBLE", "longitude": "DOUBLE", "generationtime_ms": "DOUBLE", "utc_offset_seconds": "BIGINT", "timezone": "VARCHAR", "timezone_abbreviation": "VARCHAR", "elevation": "DOUBLE",

     "time": "VARCHAR", "weather_code": "VARCHAR", "temperature_2m_max": "VARCHAR", "temperature_2m_min": "VARCHAR", "apparent_temperature_max": "VARCHAR", "apparent_temperature_min": "VARCHAR",
     "precipitation_sum": "VARCHAR", "rain_sum": "VARCHAR", "showers_sum": "VARCHAR", "snowfall_sum": "VARCHAR", "cloud_cover_mean": "VARCHAR", "wind_speed_10m_max": "VARCHAR",
     "wind_gusts_10m_max": "VARCHAR", "wind_direction_10m_dominant": "VARCHAR", "pressure_msl_mean": "VARCHAR"
   },                                                                                                                                                                                                
   "daily": {                                                                                                                                                                                        
     "time": ["VARCHAR"], "weather_code": ["UBIGINT"], "temperature_2m_max": ["DOUBLE"], "temperature_2m_min": ["DOUBLE"], "apparent_temperature_max": ["DOUBLE"],
     "apparent_temperature_min": ["DOUBLE"], "precipitation_sum": ["DOUBLE"], "rain_sum": ["DOUBLE"], "showers_sum": ["DOUBLE"], "snowfall_sum": ["DOUBLE"], "cloud_cover_mean": ["UBIGINT"],
     "wind_speed_10m_max": ["DOUBLE"], "wind_gusts_10m_max": ["DOUBLE"], "wind_direction_10m_dominant": ["UBIGINT"], "pressure_msl_mean": ["DOUBLE"]
}
```


### Training Dataset
|Column                               |Type      |
|-------------------------------------|----------|
| id                                  |  bigint  |
| month                               |  integer |
| flight_num                          |  double  |
| dest                                |  varchar |
| pred_arr_time                       |  bigint  |
| delay                               |  double  |
| origin_temperature_2m_min           |  double  |
| origin_precipitation_sum            |  double  |
| origin_snowfall_sum                 |  double  |
| origin_wind_gusts_10m_max           |  double  |
| dest_weather_code                   |  double  |
| dest_apparent_temperature_max       |  double  |
| dest_rain_sum                       |  double  |
| dest_cloud_cover_mean               |  double  |
| dest_wind_direction_10m_dominant    | double   |
|  flight_date                        | date     |
|  day_of_month                       | integer  |
|  origin                             | varchar  |
|  dest_city_name                     | varchar  |
|  pred_elapsed_time                  | double   |
|  origin_weather_code                | double   |
|  origin_apparent_temperature_max    | double   |
|  origin_rain_sum                    | double   |
|  origin_cloud_cover_mean            | double   |
|  origin_wind_direction_10m_dominant | double   |
|  dest_temperature_2m_max            | double   |
|  dest_apparent_temperature_min      | double   |
|  dest_showers_sum                   | double   |
|  dest_wind_speed_10m_max            | double   |
|  year                               |  integer |
|  day_of_week                        |  integer |
|  origin_city_name                   |  varchar |
|  pred_dep_time                      |  bigint  |
|  fl_distance                        |  double  |
|  origin_temperature_2m_max          |  double  |
|  origin_apparent_temperature_min    |  double  |
|  origin_showers_sum                 |  double  |
|  origin_wind_speed_10m_max          |  double  |
|  origin_pressure_msl_mean           |  double  |
|  dest_temperature_2m_min            |  double  |
|  dest_precipitation_sum             |  double  |
|  dest_snowfall_sum                  |  double  |
|  dest_wind_gusts_10m_max            |  double  |
| dest_pressure_msl_mean              |  double  |

---

### Delay Labels

- How is the binary delay label created?
- What delay threshold is used?
- How many examples are delayed versus not delayed?
- Does the target include only carrier/weather/NAS/security/late-aircraft delay, or total arrival delay?
- How could the label definition change future results?

---

## Graohed exploration in `backend/src/ml/training/figures/`
- Correlation: `backend/src/ml/training/figures/correlation_chart.png`
- Distribution: `backend/src/ml/training/figures/delay_distribution.png`
- Missing values (none): `backend/src/ml/training/figures/missing_values.png`

---

## Baselines

Scikit-learn's `DummyClassifier` was used as a baseline of which findings can be seen graohed in `/backend/src/ml/training/figures/dummy_strats.png`

We see `most_frequent` at ~0.97, indicating that the base model successfully predicts the majority class (no significant delay) most often. This is no suprise if you look at the distribution of delays, and the size of the training dataset.

For V1.1, I atrificually skew the train set to include a greater protion of significantly delayed flights. 

---

## Training Pipeline

Multiple pipelines have been created for each stage of data.

These being: Raw CSV -> DuckDB -> Refined DuckDB -> API Response(s) raw -> API Resposne Cleaned -> Final Training Dataset

### File key
| File Name | Premier Process | Output Table Name(s)|
|-------------------------------------------|-----------------|-------------|
|`backend/src/ml/csv_data_pipeline_funcs.py` & `backend/src/ml/csv_data_pipeline_runner.ipynb`| Process raw CSVs to usable, efficiently organised, data | `flight_data` & `airport_data`|
| | | | |
| | | | |

## Hyperparameter Tuning

- What search method is used?
- Which parameters are tuned?
- How many iterations and cross-validation folds are used?
- Which scoring metric selects the best model?
- How did you keep tuning affordable or fast enough?
- What parameters would you tune next?

## Evaluation

- Which dataset is used for final evaluation?
- What are the latest recorded metric values?
- How do the results compare to the baseline?
- Which mistakes matter most: false positives or false negatives?
- Are evaluation results reproducible?
- What does the model do well, and where does it struggle?

### Classification Metrics

- What are accuracy, precision, recall, F1, and ROC AUC for the selected model?
- Which metric is most important for interpreting this model?
- Are metrics calculated with `zero_division=0`?
- How should readers interpret a high or low precision/recall?

### Calibration

- Does `predict_proba` produce well-calibrated probabilities?
- Have you checked calibration curves or reliability diagrams?
- Should the frontend present the probability as confidence?
- Is a probability threshold other than `0.5` more useful?
- What work is needed before claiming the probability is reliable?

## Inference Pipeline

- What data does the backend collect at prediction time?
- How is AviationStack data converted into model fields?
- How is Open-Meteo data converted into model fields?
- How are categorical and numeric fields assembled?
- What dataframe columns are passed into the model?
- What happens if inference input does not match the training schema?

## Reproducibility

- Which package versions matter?
- Is dependency locking handled by `uv.lock`?
- Which random seeds are set?
- Which data files are required to reproduce training?
- Are notebooks and scripts kept in sync?
- Can someone rebuild the DuckDB tables and model from scratch using docs alone?

## Testing

- Which tests cover the CSV pipeline?
- Which tests cover schema validation?
- Which tests cover weather API behavior?
- Which tests cover the prediction service?
- Are model training and inference tested separately?
- What tests would catch a feature-name mismatch?
- What manual checks should be done after retraining?

## Known Limitations

- What are the biggest weaknesses of the training data?
- Are future flight schedules always available through the external API?
- Does the model generalize beyond 2024 US flight data?
- Does the model know about real-time operational issues?
- Are weather forecasts good enough for the prediction date?
- Which limitations should be made clear to users?

## Future Work

- What would improve data quality?
- What would improve model accuracy?
- What would improve explainability?
- What would improve request-time performance?
- What would make retraining easier?
- What would be needed for a production-ready ML workflow?
