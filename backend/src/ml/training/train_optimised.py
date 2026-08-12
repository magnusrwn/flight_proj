from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import joblib
import duckdb as ddb
from pathlib import Path

# Constants
BACKEND_ROOT = Path(__file__).resolve().parents[3]
DUCKDB_PATH = BACKEND_ROOT/"data/duck_database.duckdb"
FIGURES_PATH = BACKEND_ROOT/"src/ml/training/figures"
SIGNIFICANT_DELAY_MINUTES = 25

con = ddb.connect(DUCKDB_PATH)
data_df = con.sql("""
    SELECT * FROM model_dataset LIMIT 1000000
""").df()
con.close()

data_df = data_df.dropna(axis=0)


x_numeric_features = ['year', 'month', 'day_of_month', 'day_of_week',
        'pred_dep_time', 'pred_arr_time', 'pred_elapsed_time',
       'fl_distance', 'origin_weather_code',
       'origin_temperature_2m_max', 'origin_temperature_2m_min',
       'origin_apparent_temperature_max', 'origin_apparent_temperature_min',
       'origin_precipitation_sum', 'origin_rain_sum', 'origin_showers_sum',
       'origin_snowfall_sum', 'origin_cloud_cover_mean',
       'origin_wind_speed_10m_max', 'origin_wind_gusts_10m_max',
       'origin_wind_direction_10m_dominant', 'origin_pressure_msl_mean',
       'dest_weather_code', 'dest_temperature_2m_max',
       'dest_temperature_2m_min', 'dest_apparent_temperature_max',
       'dest_apparent_temperature_min', 'dest_precipitation_sum',
       'dest_rain_sum', 'dest_showers_sum', 'dest_snowfall_sum',
       'dest_cloud_cover_mean', 'dest_wind_speed_10m_max',
       'dest_wind_gusts_10m_max', 'dest_wind_direction_10m_dominant',
       'dest_pressure_msl_mean']
x_categorical_features = ['flight_date', 'origin', 'dest']
x_features = x_numeric_features + x_categorical_features

X = data_df[x_features]
y = (data_df["delay"] >= SIGNIFICANT_DELAY_MINUTES).astype(int)

print(f"Significant delay threshold: {SIGNIFICANT_DELAY_MINUTES} minutes")
print(y.value_counts(normalize=True).rename({0: "not_significant", 1: "significant"}))

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=1,
    stratify=y,
)

best_params = {
    "classifier__n_estimators": 350,
    "classifier__min_samples_split": 20,
    "classifier__min_samples_leaf": 10,
    "classifier__max_samples": 0.9,
    "classifier__max_features": 0.5,
    "classifier__max_depth": 18,
    "classifier__class_weight": 'balanced_subsample',
    "classifier__bootstrap": True
}

preprocessor = ColumnTransformer(
    transformers=[
        ("categorical", OneHotEncoder(handle_unknown="ignore"), x_categorical_features),
        ("numeric", "passthrough", x_numeric_features),
    ]
)

pipeline = Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("classifier", RandomForestClassifier(n_jobs=1, random_state=1)),
    ]
)

pipeline.set_params(**best_params)
pipeline.fit(X_train, y_train)

try:
    joblib.dump(pipeline, str(BACKEND_ROOT/"src/ml/model/model.joblib"))
    print(f"SAVED model to {str(BACKEND_ROOT/"src/ml/model/model.joblib")}")
except:
    print(f"Could NOT save model to {str(BACKEND_ROOT/"src/ml/model/model.joblib")}")
