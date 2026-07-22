import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PATH_TO_FLIGHT_DATA = DATA_DIR / "flight/cleaned_flight_sample_data.csv"
PATH_TO_AIRPORT_DATA = DATA_DIR / "airport/airport.csv"

# Get airport data to a DF
flights = pd.read_csv(PATH_TO_FLIGHT_DATA)
airports = pd.read_csv(PATH_TO_AIRPORT_DATA)

# Create a table for date + origin, and date + dest
flight_date_w_origin = (
    flights[["origin", "fl_date", "origin_long", "origin_lat"]]
    .rename(columns={
        "origin":"airport_code",
        "origin_long":"long",
        "origin_lat":"lat"
    })
    .dropna()
    .drop_duplicates()
)

flight_date_w_dest = (
    flights[["dest", "fl_date", "dest_long", "dest_lat"]]
    .rename(columns={
        "dest":"airport_code",
        "dest_long":"long",
        "dest_lat":"lat"
    })
    .dropna()
    .drop_duplicates()
)

airports_w_dates = pd.concat(
    [flight_date_w_origin, flight_date_w_dest],
    ignore_index=True
).dropna().drop_duplicates(subset=["fl_date", "airport_code"])

# Now match with the airports table for the airport name(s)
airport_full_names = airports.loc[
    airports["iata_code"].isin(airports_w_dates["airport_code"]),
    [
        "iata_code",
        "name"
    ]
].rename(columns={
    "iata_code":"airport_code",
    "name":"airport_full_name"
}).copy()

complete_table_for_weather_api = airport_full_names.merge(
    airports_w_dates,
    left_on="airport_code",
    right_on="airport_code",
)


# === MERGE TO FLIGHTS TABLE (efficiently) ===
airport_full_names = airport_full_names[["airport_code", "airport_full_name"]].dropna().drop_duplicates(subset=["airport_code", "airport_full_name"])

# flights origin merge
flights = flights.merge(
    airport_full_names,
    left_on="origin",
    right_on="airport_code",
    validate="many_to_one"
).drop(columns="airport_code"
).rename(columns={
    "airport_full_name":"origin_airport_full_name"
    })

# flights destination merge
flights = flights.merge(
    airport_full_names,
    left_on="dest",
    right_on="airport_code",
    validate="many_to_one"
).drop(columns="airport_code"
).rename(
    columns={"airport_full_name":"dest_airport_full_name"}
)

# save the new and updated flights data AND the data for weather_api...
flights.to_csv(DATA_DIR/"flight/cleaned_flight_sample_data_with_airports.csv")
complete_table_for_weather_api.to_csv(DATA_DIR/"airport/airport_data_for_weather_api.csv")