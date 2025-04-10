import pandas as pd
import re
import os

def add_artist_list(df, output_path="chart-data/cleaned_charts.csv"):
    # Define common separators
    separators = ['feat.', 'ft.', '&', ',', '+', '/']
    # Compile regex pattern to split on separators (case insensitive)
    pattern = r'\s*(?:' + '|'.join(map(re.escape, separators)) + r')\s*'

    # Create a new column with list of artists
    df['artist_list'] = df['artist'].astype(str).apply(
        lambda x: [artist.strip() for artist in re.split(pattern, x, flags=re.IGNORECASE)]
    )

    # Save to a new CSV
    df.to_csv(output_path, index=False)
    return df

def load_cleaned_data():
    if os.path.exists('chart-data/cleaned_charts.csv'):
        df = pd.read_csv("chart-data/cleaned_charts.csv")
    else:
        df = pd.read_csv("chart-data/singles_charts_2010s.csv")
        df = add_artist_list(df)

    return df