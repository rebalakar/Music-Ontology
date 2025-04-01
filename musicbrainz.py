import musicbrainzngs
import json
import pandas as pd
import time

# Setup MusicBrainz client
musicbrainzngs.set_useragent("ChartKGBuilder", "1.0", "email@example.com")

# Load the cleaned CSV
df = pd.read_csv("singles_charts_2010s_cleaned.csv")

# Prepare dictionary to hold all results and a set to track processed entries
all_filtered = {}
seen_entries = set()

for i, row in df.iterrows():
    song_title = row['song'].strip()
    artist_name = row['artist'].strip()
    key = f"{song_title.lower()} - {artist_name.lower()}"
    print(f'Getting data for {song_title} by {artist_name}')

    # Skip duplicates
    if key in seen_entries:
        continue
    seen_entries.add(key)

    filtered = {}

    try:
        # Query work
        work = musicbrainzngs.search_works(artist=artist_name, recording=song_title, limit=1)
        time.sleep(1)

        if not work['work-list']:
            continue  # Skip if no work found

        work_data = work['work-list'][0]
        filtered['track'] = work_data.get('title', '')
        filtered['language'] = work_data.get('language', '')

        # Related people
        artist_relations = work_data.get("artist-relation-list", [])
        for rel in artist_relations:
            rel_type = rel.get("type")
            rel_artist_name = rel.get("artist", {}).get("name")
            if rel_type and rel_artist_name:
                if rel_type in filtered:
                    filtered[rel_type].append(rel_artist_name)
                else:
                    filtered[rel_type] = [rel_artist_name]

        # Get tags
        work_id = work_data.get("id")
        tags = musicbrainzngs.get_work_by_id(work_id, includes=['tags'])
        time.sleep(1)
        tag_list = tags['work'].get('tag-list', [])
        filtered['tags'] = [tag['name'] for tag in tag_list] if tag_list else []

        # Get artist IDs
        recording = musicbrainzngs.search_recordings(artist=artist_name, recording=song_title, limit=1)
        time.sleep(1)

        if not recording['recording-list']:
            continue  # Skip if no recording found

        artist_ids = [
            entry['artist']['id']
            for entry in recording['recording-list'][0].get('artist-credit', [])
            if isinstance(entry, dict) and 'artist' in entry
        ]

        # Get artist details
        artist_list = []
        for artist_id in artist_ids:
            artist = musicbrainzngs.get_artist_by_id(artist_id, includes=['aliases'])
            time.sleep(1)

            legal_names = [
                alias['alias']
                for alias in artist["artist"].get("alias-list", [])
                if alias.get("type") == "Legal name"
            ]

            artist_list.append({
                'artist_name': artist["artist"]["name"],
                'legal_name': legal_names,
                'gender': artist["artist"].get("gender", "")
            })

        filtered['artist'] = artist_list
        all_filtered[f"{song_title} by {artist_name}"] = filtered

    except Exception as e:
        print(f"Error on '{song_title}' by '{artist_name}': {e}")

# -----------------------------
# Normalize structure
# -----------------------------
# Determine all possible artist relation types
all_relation_types = set()
for entry in all_filtered.values():
    all_relation_types.update(k for k in entry.keys() if k not in {'track', 'language', 'tags', 'artist'})

# Define structure
filler = "N/A"
standard_keys = ['track', 'language', 'tags'] + sorted(all_relation_types) + ['artist']
artist_fields = ['artist_name', 'legal_name', 'gender']

for entry in all_filtered.values():
    # Fill missing top-level keys
    for key in standard_keys:
        if key not in entry:
            entry[key] = [] if key in all_relation_types or key == 'tags' else filler

    # Normalize artist fields
    for artist in entry['artist']:
        for field in artist_fields:
            if field not in artist:
                artist[field] = [] if field == 'legal_name' else filler

# -----------------------------
# Save output
# -----------------------------
with open("filtered_all.json", "w") as f:
    json.dump(all_filtered, f, indent=2)

print("Data collection complete and saved to 'filtered_all.json'")