import musicbrainzngs
import json
import ast
import os

from musicbrainz.filters import get_most_similar
from musicbrainz.utils import select_recording, get_work_data, get_artist_data
from musicbrainz.data_utils import load_cleaned_data
from musicbrainz.format_recording import format_recording

def main():
    # Setup MusicBrainz client
    musicbrainzngs.set_useragent("ChartKGBuilder", "1.0", "email@example.com")

    # Load cleaned csv
    df = load_cleaned_data()

    # Load checkpoint (if it exists)
    existing_data_path = 'formatted_data.json'
    if os.path.exists(existing_data_path):
        print('Starting from checkpoint')
        with open(existing_data_path, 'r', encoding='utf-8') as f:
            formatted_data = json.load(f)
        seen_entries = set(formatted_data.keys())
    else:
        print('Starting from the beginning')
        seen_entries = set()

    formatted_data = {}
    tie_entries = {}

    # Loop through each row in the csv
    for i, row in df.iterrows():
        query_artist_list = ast.literal_eval(row['artist_list'])
        query_song = row['song'].strip()
        query_artists_str = ", ".join(name.lower() for name in query_artist_list)
        key = f"{query_song} - {query_artist_list}"

        if key in seen_entries:
            print(f'Skipping - Already searched for {query_song} by {query_artist_list}')
            print('-'*50)
            continue
        seen_entries.add(key)

        # Search musicbrainz and return recordings that are most similar to the queries
        print(f'Searching MusicBrainz for {query_song} by {query_artist_list}')
        most_similar = get_most_similar(query_song, query_artist_list, query_artists_str)

        # Select the most likely match
        selected_recording, tie = select_recording(most_similar)
        # Select first if there is a tie
        if tie:
            print('Still more than one possible recording - taking the first one')
            tie_entries[key] = selected_recording
            selected_recording = selected_recording[0]
        
        # Add full work data
        selected_recording['work_data'] = get_work_data(selected_recording)

        # Add full artist data
        selected_recording['artist_data'] = get_artist_data(selected_recording)

        # Format recording
        formatted_recording = format_recording(selected_recording)

        # Add to formatted data
        formatted_data[key] = formatted_recording

        print('-'*50)
        # Save every 10 new entries
        if len(list(seen_entries)) % 10 == 0 or i == df.index[-1]:
            with open("formatted_data.json", "w") as f:
                json.dump(formatted_data, f, indent=2)

if __name__ == "__main__":
    main()