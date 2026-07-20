from pathlib import Path
import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
S_FLIGHTS_DATA = DATA_DIR + "/flight/cleaned_airport_data_sample.csv" #NOTE: sample atm
AIRPORT_DATA = DATA_DIR + "/airport/airports_sorted.csv"
WEATHER_API_DATA = DATA_DIR + "/weather/weather_api_responses.csv"
OUTPUT_DATA = DATA_DIR + "/output/flight_data_2024_sample_with_weather.csv"

def map_weather_to_airports(airports: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    airport_columns = {"date", "ap_code", "lat", "long"}
    weather_columns = {"daily_time", "latitude", "longitude"}
    
    if missing := airport_columns - set(airports.columns):
        raise ValueError(f"Airport lookup is missing columns: {sorted(missing)}")
    if missing := weather_columns - set(weather.columns):
        raise ValueError(f"Weather data is missing columns: {sorted(missing)}")

    airports = airports.loc[:, ["date", "ap_code", "lat", "long"]].copy()
    airports["date"] = pd.to_datetime(airports["date"]).dt.date
    weather = weather.copy()
    weather["date"] = pd.to_datetime(weather["daily_time"]).dt.date

    mapped = weather.merge(
        airports,
        left_on=["date", "lat", "long"],
        right_on=["date", "longitude", "latitude"],
        how="inner"
    )

    if mapped.empty:
        raise ValueError("No weather rows could be mapped to an airport lookup.")
    if mapped.duplicated(["date", "ap_code"]).any():
        raise ValueError("Multiple weather rows mapped to the same airport and date.")

    return mapped

def attach_weather(flights: pd.DataFrame, mapped_weather: pd.DataFrame, airport_code_column: str, prefix: str) -> pd.DataFrame:
    """Join a prefixed copy of mapped weather (weather with dates, and airport) to one flight-airport column."""
    weather_columns = [
        column
        for column in mapped_weather.columns
        if column not in {"weather_index", "date", "ap_code", "daily_time"}
        and not column.startswith("daily_units_")
    ]

    weather_for_join = mapped_weather.loc[:, ["date", "ap_code", *weather_columns]].copy()
    weather_for_join["weather_date"] = mapped_weather["daily_time"] # NOTE: is this needed? I already haev flight date -- seen in above
    weather_for_join = weather_for_join.rename(
        columns={
            "date": "fl_date",
            "ap_code": airport_code_column,
            "weather_date": f"{prefix}_date",
        }
    )
    return flights.merge(
        weather_for_join,
        on=["fl_date", airport_code_column],
        how="left",
        validate="many_to_one",
    )

def main() -> None:
    weather = pd.read_csv(WEATHER_API_DATA)
    flights = pd.read_csv(S_FLIGHTS_DATA)
    airports = pd.read_csv(AIRPORT_DATA)
    # Make copy, as will be keeping the origional .CSV (not overwriting)
    flights_c = flights.copy()
    flights_c["fl_date"] = pd.to_datetime(flights_c["fl_date"]).dt.date

    mapped_weather = map_weather_to_airports(airports, weather)
    flights_c = attach_weather(flights_c, mapped_weather, "origin", "origin_weather")
    flights_c = attach_weather(flights_c, mapped_weather, "dest", "dest_weather")

    # TODO: Write differently/ make pd.Df that will be written in dif way
    # args.output.parent.mkdir(parents=True, exist_ok=True)
    output_address = DATA_DIR + "/output/data_sample_final.csv"
    flights_c.to_csv(output_address, index=False)

    # TODO: Remake output msgs
    origin_matched = flights_c["origin_weather_weather_code"].notna().sum()
    destination_matched = flights_c["dest_weather_weather_code"].notna().sum()
    print(f"Finished sorting process. Stats...\nOrigins matched: {origin_matched}\nDestinations matched: {destination_matched}")
    
    print("\n\n=====TERMINATED=====\n\n")

if __name__ == "__main__":
    main()
