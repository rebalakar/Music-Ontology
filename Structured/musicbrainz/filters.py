import time
from datetime import datetime
import musicbrainzngs
from rapidfuzz import fuzz

from Structured.musicbrainz.utils import get_release_dates

def get_most_similar(query_song, query_artist_list, query_artists_str):
    query_artist = query_artist_list[0] # Use first artist for query
    results = musicbrainzngs.search_recordings(recording=query_song, artist=query_artist)
    time.sleep(1)
    print(f'{len(results.get('recording-list', []))} results found')
    
    most_similar = []
    max_score = 0

    for r in results.get('recording-list', []):
        result_names = [
            artist['artist']['name'].lower()
            for artist in r.get('artist-credit', [])
            if isinstance(artist, dict) and 'artist' in artist and 'name' in artist['artist']
        ]
        result_artists_str = ", ".join(result_names)

        title_score = fuzz.ratio(r['title'], query_song)
        artist_score = fuzz.ratio(query_artists_str, result_artists_str)
        combined_score = title_score + artist_score

        if combined_score > max_score:
            max_score = combined_score
            most_similar = [r]
        elif combined_score == max_score:
            most_similar.append(r)
        
    print(f'Filtered down to {len(most_similar)} recordings')
    return most_similar

def get_most_artists(recording_list):
    max_artists = 0
    most_artists = []
    for r in recording_list:
        # Get recording by ID from MusicBrainz with artist relations list
        recording = musicbrainzngs.get_recording_by_id(
            r['id'], 
            includes=['artist-rels', 'tags', 'artist-credits', 'work-rels', 'releases', 'label-rels']
        )['recording']
        time.sleep

        # Find release with the longest artist relations list
        artist_relations = recording.get("artist-relation-list", [])
        if len(artist_relations) > max_artists:
            max_artists = len(artist_relations)
            most_artists = [recording]
        elif len(artist_relations) == max_artists:
            most_artists.append(recording)

    print(f'{len(most_artists)} recordings with {max_artists} associated people')
    return most_artists

def get_earliest_recordings(recording_list):
    earliest_recordings = []
    min_earliest = datetime.max
    for r in recording_list:
        full_dates = get_release_dates(r)
        # Find the earliest release for each recording
        if full_dates:
            parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in full_dates]
            earliest_date = min(parsed_dates)
            if earliest_date < min_earliest:
                min_earliest = earliest_date
                earliest_recordings = [r]
            elif earliest_date == min_earliest:
                earliest_recordings.append(r)
        else:
            print('No releases with full dates')
            return None
    
    print(f'{len(earliest_recordings)} recordings with {min_earliest} release date')
    return earliest_recordings

def get_most_releases(recording_list):
    max_releases = 0
    most_releases = []
    for r in recording_list:
        num_releases = len(r.get('release-list', []))
        if num_releases > max_releases:
            max_releases = num_releases
            most_releases = [r]
        elif num_releases == max_releases:
            most_releases.append(r)

    print(f'{len(most_releases)} recordings with {max_releases} releases')
    return most_releases