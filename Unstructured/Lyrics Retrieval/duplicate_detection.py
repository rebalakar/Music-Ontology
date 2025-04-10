import pandas as pd

# Load the CSV file
df = pd.read_csv("singles_charts_2010s.csv")

# Create a new column that combines artist and song
df["artist_song"] = df["artist"].str.strip() + " - " + df["song"].str.strip()

# Count duplicates
duplicate_counts = df["artist_song"].value_counts()
duplicates = duplicate_counts[duplicate_counts > 1]

if not duplicates.empty:
    print("Duplicate songs found:")
    print(duplicates)
else:
    print("No duplicate songs found.")
