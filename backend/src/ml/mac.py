import pandas as pd
from pathlib import Path

PATH_TO_CSV = Path(__file__).resolve().parents[2]/"data/csv/flight_data_2024_sample.csv"


r = pd.read_csv(PATH_TO_CSV)
print(r.columns)

