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

- What real-world problem are you trying to solve?
- Why is flight delay prediction useful or interesting?
- Is this a classification problem, regression problem, or both at different stages?
- What is the prediction made before the flight departs?
- What assumptions are you making about what data is available before departure?

## Prediction Target

- What exact target variable does the model learn?
- How is `total_delay` or `delay` calculated from raw flight data?
- What threshold defines a significant delay?
- Why was that threshold chosen?
- Does the model predict any delay, a significant delay, or delay duration?
- What does class `0` mean, and what does class `1` mean?

## Success Metrics

- Which metrics do you use to judge the model?
- Why are accuracy, precision, recall, F1, and ROC AUC useful or limited here?
- Which metric matters most for this project, and why?
- What baseline should the trained model beat?
- What score would be good enough for a demo or portfolio project?
- How should class imbalance affect metric choice?

---

## Data Sources
**APIs Used:**
- [Open-Meteo API](https://open-meteo.com) for all weather data. *Rate limits
- [Aviation Stack API](https://docs.apilayer.com/aviationstack/docs/api-documentation) for future flight schedule information. * Strong rate limits

**Datasets Used**
- Kaggle [2024 USA flighs](https://www.kaggle.com/datasets/hrishitpatil/flight-data-2024/data) convering each flight in the USA during the year 2024.
- [Americaon airports dataset](https://data.humdata.org/dataset/ourairports-usa) from the HDX (UN data project) showing each airport in the USA.

---

## Dataset descriptions

---

### Weather Data

- Which Open-Meteo product is used for training data?
- Which Open-Meteo product is used at prediction time?
- What daily weather variables are requested?
- Why are weather features collected for both origin and destination?
- How are failed weather requests tracked?
- Are weather values historical observations, forecasts, or API-provided estimates?

## Data Schema

- Which cleaned tables exist in DuckDB?
- Which schema is expected for each table?
- Which Pydantic models define the expected table columns?
- What columns are required to build the training dataset?
- Which column names must stay stable because the model depends on them?

### Raw Flight Columns

- Which raw CSV columns are required by `create_and_clean_flights_table`?
- What type is each important raw column before cleaning?
- Which delay columns are combined?
- Which rows are filtered out before training?
- Are there raw columns that look useful but were intentionally not used?

### Raw Airport Columns

- Which raw airport CSV columns are required?
- How are raw latitude and longitude renamed?
- How is the IATA code normalized or filtered?
- Which rows are excluded?
- What source-specific assumptions does the cleaning code make?

### Weather Features

- What weather fields are requested from Open-Meteo?
- What units does each weather field use?
- Are the weather values daily summaries, hourly values, or current conditions?
- How are origin weather feature names prefixed?
- How are destination weather feature names prefixed?
- What should happen if a weather field is missing?

### Training Dataset

- How is the final `model_dataset` table built?
- Which tables are joined together?
- What join keys are used?
- How are flight rows matched to weather rows?
- How many rows are used for training?
- Are any rows dropped because of nulls?

## Data Cleaning

- What cleaning steps happen before model training?
- Which rows are removed and why?
- Which columns are cast to new types?
- How are missing delay values handled?
- How are schema mismatches detected?
- What data cleaning choices could bias the model?

## Feature Engineering

- Which raw fields become model features?
- Which features are directly copied from cleaned data?
- Which features are calculated?
- Which features are categorical?
- Which features are numeric?
- Which features were considered but not included?

### Date and Time Features

- How are `year`, `month`, `day_of_month`, and `day_of_week` created?
- How are scheduled departure and arrival times represented?
- How is elapsed time calculated?
- How are overnight flights handled?
- Why is `flight_date` treated as a categorical feature in the current pipeline?

### Airport Features

- Which airport-related features are used?
- Are airport codes used as categorical variables?
- Are city names used or only kept for response/debugging?
- Are latitude and longitude used directly by the model?
- Are coordinates used to calculate flight distance?

### Route Features

- How is flight distance calculated?
- Is the route represented by origin and destination separately or as a combined route?
- Are airline or flight number features used?
- Could route popularity or airport congestion be useful future features?

### Weather Features

- Which weather features are included for origin?
- Which weather features are included for destination?
- Are weather features normalized, scaled, or passed through directly?
- Are interactions like snow plus wind considered?
- Which weather features seem most useful based on exploration?

### Delay Labels

- How is the binary delay label created?
- What delay threshold is used?
- How many examples are delayed versus not delayed?
- Does the target include only carrier/weather/NAS/security/late-aircraft delay, or total arrival delay?
- How could the label definition change future results?

## Exploratory Data Analysis

- What questions did you ask during EDA?
- Which figures are generated?
- Where are the figures saved?
- What did you learn from the plots?
- Which findings influenced feature engineering or model choice?

### Missing Values
Missing values have been found to be rare. In the odd/ uncaught case of missing values, the dataset is more than large enoguh (for my intentions/ AWS compute budget) to drop the entire row.
⚠️ RREMEMBER: explain the output image of no cols dropped

### Class Balance

- What percentage of flights are significant delays?
- Is the dataset imbalanced?
- Which dummy baseline performs best?
- How does class balance affect precision, recall, and F1?
- Did you use class weights to address imbalance?

### Correlations

- Which numeric features correlate most with delay?
- Are any correlations surprising?
- Are correlations strong enough to explain the model alone?
- Which useful relationships might not appear in simple linear correlation?

### Delay Distribution

- What does the delay distribution look like?
- Are early arrivals included?
- Are extreme delays common or rare?
- Where does the significant-delay threshold sit in the distribution?
- Does the distribution suggest outlier handling?

## Train Validation Test Split

- How is the data split into training and test sets?
- What `test_size` and `random_state` are used?
- Is the split stratified by the delay label?
- Is there a separate validation set, or does cross-validation provide validation?
- Could a time-based split be more realistic than a random split?
- What leakage risks exist when splitting flight data?

## Baselines

- Which dummy classifiers are tested?
- What baseline scores are recorded?
- Which baseline is the main comparison point?
- Does the random forest beat the baseline on the metric that matters?
- What would a simple rule-based baseline look like?

## Model Selection

- Why did you choose a random forest classifier?
- What strengths does random forest have for this dataset?
- What weaknesses does it have?
- What preprocessing is needed for numeric and categorical columns?
- Which other models were considered?

### Random Forest Classifier

- What scikit-learn pipeline is used?
- How are categorical variables encoded?
- How are numeric variables handled?
- What hyperparameters are searched?
- Why are `class_weight`, `max_depth`, `n_estimators`, and `max_samples` relevant?
- How expensive is training?

### Alternative Models Considered

- Did you consider logistic regression, gradient boosting, XGBoost/LightGBM, neural networks, or regression models?
- Why were they not chosen for the current version?
- What would you try next if model performance is not good enough?
- Which alternatives would improve explainability, speed, or accuracy?

## Training Pipeline

- Which script or notebook is the source of truth for training?
- What command should a developer run to train the model?
- What inputs must exist before training starts?
- What outputs are produced?
- Does training save the model artifact automatically?
- Where are metrics and plots written?

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

### Confusion Matrix

- What are the counts for true positives, false positives, true negatives, and false negatives?
- Which error type is more common?
- Which error type is more harmful for this use case?
- Does the confusion matrix change with a different threshold?

### Feature Importance

- Which features does the random forest rely on most?
- Are importances stable across training runs?
- Are categorical airport features dominating the model?
- Do important features make domain sense?
- Would permutation importance or SHAP give a better explanation?

## Model Artifacts

- What file stores the trained model?
- Does the file include preprocessing and classifier together?
- How is the model loaded by the backend?
- How should the artifact be regenerated?
- Should model artifacts be committed or recreated locally?
- How will you avoid training/inference feature drift?

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

## Monitoring

- If deployed, what should be monitored?
- Should you track request errors, latency, API failures, and model exceptions?
- Should you log prediction distributions over time?
- How would you detect data drift or degraded model quality?
- What metrics would matter for a portfolio/demo deployment?

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
