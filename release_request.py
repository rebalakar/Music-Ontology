import requests
import json

def search_release(artist_mbid):
    base_url = f"https://musicbrainz.org/ws/2/release-group"
    headers = {"User-Agent": "MusicGraphPipeline/1.0 (mmarthoz@gmail.com)"}

    params = {
        "artist": artist_mbid,
        "fmt": "json"
    }
    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()
    release_details = data['release-groups']

    release_json = {}

    # Process up to 10 releases
    for i, r in enumerate(release_details[:10]):
        release_json[r["title"]] = {
            "id": r.get("id"),
            "artist": "The Weeknd",
            "title": r.get("title"),
            "first-release-date": r.get("first-release-date"),
            "primary-type": r.get("primary-type"),
            "secondary-types": r.get("secondary-types", [])
        }

    with open("release.json", "w") as f:
        json.dump(release_json, f, indent=4)

example = "c8b03190-306c-4120-bb0b-6f2ebfc06ea9"
search_release(example)