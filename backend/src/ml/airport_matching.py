import pandas as pd

# Read the saved data. (gathered from juypiter script(s))
PATH_TO_DATA = '/Users/magnusnewton/Desktop/code/storm_proj/backend/data/cleaned_data.csv'

# Get the data to a DF
df = pd.read_csv(PATH_TO_DATA)

# Create origin 'o' and dest 'd'
o = df[["fl_date", "origin", "origin_long", "origin_lat"]].rename(
    columns={
        "fl_date":"date",
        "origin":"ap_code",
        "origin_long":"long",
        "origin_lat":"lat"
    }
)

d = df[["fl_date", "dest", "dest_long", "dest_lat"]].rename(
    columns={
        "fl_date":"date",
        "dest":"ap_code",
        "dest_long":"long",
        "dest_lat":"lat"
    }
)

unique_lookups_df = (
    pd.concat([o, d], ignore_index=True)
    .drop_duplicates()
    .reset_index(drop=True)
)

try:
    unique_lookups_df.to_csv('./data/airports_sorted.csv') # rememebr to run when in /backend
    print("saved")
except Exception as e:
    print(f"Error caught while saving to .csv: {e}")
finally:
    print("Process terminated.")