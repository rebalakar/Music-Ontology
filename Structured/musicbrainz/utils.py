import time
import musicbrainzngs

import Structured.musicbrainz.filters as filters

def select_recording(recording_list):
    tie = False
    # Pipeline to select recording
    if len(recording_list) == 1:
        print('Only one recording with highest combined similarity score')
        selected_recording = recording_list[0]
    else:
        most_artists = filters.get_most_artists(recording_list)
        if not most_artists:
            most_artists = recording_list
        if len(most_artists) == 1:
            print('Stopping recording selection at most artists')
            selected_recording = most_artists[0]
        else:
            earliest_recording = filters.get_earliest_recordings(most_artists)
            if not earliest_recording:
                earliest_recording = most_artists
            if len(earliest_recording) == 1:
                print('Stopping recording selection at earliest recording')
                selected_recording = earliest_recording[0]
            else:
                most_releases = filters.get_most_releases(earliest_recording)
                if not most_releases:
                    most_releases = earliest_recording
                if len(most_releases) == 1:
                    print('Stopping recording selection at most releases')
                    selected_recording = most_releases[0]
                else:
                    tie = True
    return selected_recording, tie

def get_release_dates(recording):
    # Get all release dates for each recording
    release_dates = [
        release['date']
        for release in recording.get('release-list', [])
        if 'date' in release
    ]
    # Filter for dates that are in the right format
    full_dates = [d for d in release_dates if len(d) == 10 and '-' in d]

    return full_dates

def get_work_data(selected_recording):
    if 'work-relation-list' in selected_recording:
        work_relation = selected_recording['work-relation-list'][0]
        if isinstance(work_relation, dict) and 'work' in work_relation:
            work_id = work_relation['work']['id']
            print(f'Loading work data')
            work_data = musicbrainzngs.get_work_by_id(work_id, includes=['artist-rels'])
            time.sleep(1)
        work = work_data.get('work')
        return work
    
def get_artist_data(selected_recording):
    artist_entries = []

    if 'artist-credit' in selected_recording:
        for credit in selected_recording['artist-credit']:
            if isinstance(credit, dict) and 'artist' in credit:
                artist_id = credit['artist']['id']
                print(f'Loading {credit['artist']['name']}')
                artist_data = musicbrainzngs.get_artist_by_id(artist_id, includes=['aliases'])
                time.sleep(1)
                artist_entries.append(artist_data['artist'])
    return artist_entries