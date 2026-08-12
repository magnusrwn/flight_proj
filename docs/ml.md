## Overview
- This model takes in the weather and flight data, and outputs a prediction on the flight being significantly delayed (>25min), or not.
- The Model is used within the `flight_prediction_sercive.py` file which holds the main function/ logic for the endpoint `/predict`
- The model is downloadable in the g-drive link, located [here](https://drive.google.com/file/d/1KRhr2aaH5HY-2BNteX0C7LtocAqY2zGC/view?usp=sharing)
- To see input, see `MLModelInput` in file `backend/src/models/base_models.py`

---

## Model setup (if you want to train it -- not reccomended):
- Open a new terminal and `cd` to `/backend`, if not already there
- Install `uv` if you do not have it alrady
- Run the command `uv sync`
- Ensure your .env is setup (see '.env Configuration' [here](https://github.com/magnusrwn/flight_proj/blob/main/README.md) on how to do that)
- Run pipeline file(s):
    - CSV pipeline runner(1st): `backend/src/ml/csv_data_pipeline_funcs.py`
    - **Note:**: For the following 2 steps: I ran these on EC2 with tmux so I did not have to wait for the API responses/ training. Do as you whish.
    - Weather API runner (2nd): `backend/src/ml/weather_api_data_runner.py`
    - Run `backend/src/ml/training/train.ipynb` to replicate my process exactly or `backend/src/ml/training/train_optimised.py` to train the optimised model


### **or**
Just download it from google drive [here](https://drive.google.com/file/d/1KRhr2aaH5HY-2BNteX0C7LtocAqY2zGC/view?usp=sharing). Then place it in `backend/src/ml/model/` keeping its name as `model.joblib`

---

## Problem Definition
For predicting an exact delay, regression would usually be the prefered way. However, that being said, after training and tring to tune regressive random forests I discorvered it's quite hard to get notably better than taking hte average of the training data.

Thus, I thoguht that making hte delay a binary would be beneficial for the training results, allowing for a higher probability of actual utility. This change can be seen clearly in `/backend/src/ml/train/train.ipynb`.

The model preformed better than taking the avg when the Y was turned into a binary and the model switched to a classifier however, still has room for improvement.

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

## Graphed exploration in `backend/src/ml/training/figures/`
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
| File Name | Premier Process | Output DuckDB Table Name(s)|
|-------------------------------------------|-----------------|-------------|
| **`backend/src/ml/csv_data_pipeline_funcs.py`** & **`backend/src/ml/csv_data_pipeline_runner.ipynb`** | Process raw CSVs to usable, efficiently organised, data | `flight_data` & `airport_data`|
| **`backend/src/ml/weather_api_data_runner.py`** & **`backend/src/ml/weather_api_data_pipeline_funcs.py`** | Create and process `weather_req_table` for efficient and easy weather API requests and creation of `model_dataset`| `weather_response_raw` & `model_dataset` |

---

## Hyperparameter Tuning

Scikit-learn's `RandomizedSearchCV` was used for hyperparameter tuning with 3 cross validation folds, and can be seen in the 'training' section of `/backend/src/ml/training/train.ipynb`.

See the output of the bese params in `backend/src/ml/training/figures/train_results/best_results.txt`

The training/ tuning was ran on EC2. I would highly recommend this, as otherwise it will take a long while.

---

## Evaluation

Resuts shown in `backend/src/ml/training/figures/train_results/best_results.txt` are as follows:
| Metric    | Value |
| --------- | ----- | 
| Accuracy  | 0.780 |
| Precision | 0.420 |
| Recall    | 0.528 |
| F1        | 0.468 |
| ROC AUC   | 0.758 |
| CV F1     | 0.461 |


- Note of evaluation: CV F1 / F1 are similar, indicating that the models results/ outputs are a very replica of actual ability.

---

## Testing

- Find all tests clearly named/ labeled in `backend/tests/`

---

## Known Limitations

*Limitations/ evaluations of data and training method*
- 2024 data could have been more up to date
    - However, note that this would have meant a more complex pipeline with more fragmented data
- Weather data could have been more exact. Currently it's limited to daily sumaries.
    - A change could mean quereing for the scheduled landing times slots (with a time buffer), or/ and maybe weather of the day(s) prior. This could indicate that a large weather event could have passed recently, or that quick-passing sever conditions could make the journey more dificult
- Predictions are based purely on the weather
    - Currently, the only histirical/ sitiational information to make a predictions is from the weather on the day, and the general flight information. If information, such as previous flights from that gate, day, or route, were given, prediction would likely be must more accurate.

**Summary**: Narrow data limited by depth (summaries or/and lack of historical comparison)

---

## Future Work
- Improve data quality
- Cross reference/ gather more data from mroe sources
- Migrate away from Aviation Stack API
- Create a flight-saving pipeleine, which tracks current flights and fills in fields for training (gathers weather, historicals, etc...)
- Orient the API to be for production, not a locally hosted project

Keep eyes on [Issues](https://github.com/magnusrwn/flight_proj/issues) for the things on the todo list