import requests
import json

def search_artist(artist_name):
    base_url = "https://musicbrainz.org/ws/2/artist"
    headers = {"User-Agent": "MusicGraphPipeline/1.0 (mmarthoz@gmail.com)"}

    params = {
        "query": artist_name,
        "fmt": "json"
    }
    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()
    artist_details = data["artists"][0]

    with open("artist.json", "w") as f:
        json.dump(artist_details, f, indent=4)

example = "The Weeknd"
search_artist(example)