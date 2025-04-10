import difflib
import re
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from data_loader import normalize_name, normalize_title, generate_entity_id

def clean_title(title):
    """Clean up a title for better matching"""
    # Replace non-alphanumeric characters with spaces
    title = re.sub(r'[^\w\s]', ' ', title)
    
    # Remove common words and prefixes/suffixes
    common_words = ['the', 'a', 'an', 'feat', 'ft', 'featuring', 'prod', 'by', 'with']
    title_parts = title.lower().split()
    title_parts = [part for part in title_parts if part not in common_words]
    
    # Rejoin with spaces and clean up extra spaces
    title = ' '.join(title_parts)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title.lower()

def normalize_artist_name(name):
    """Normalize artist name for better matching"""
    # Remove featuring artists, common suffixes, etc.
    name = re.sub(r'\s+(?:feat|ft|featuring)\.?\s+.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+&\s+.*', '', name)
    name = re.sub(r'\s+and\s+.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r',.*', '', name)
    
    # Remove words in parentheses
    name = re.sub(r'\([^)]*\)', '', name)
    
    # Remove common prefixes
    prefixes = ['dj ', 'mc ', 'lil ', 'young ', 'big ', 'tha ', 'the ']
    for prefix in prefixes:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
    
    # Remove special characters
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Convert to lowercase
    return name.lower()

def extract_first_artist(artist_text):
    """Extract the primary artist from a string that might contain multiple artists"""
    # Handle various forms of artist collaborations
    if " feat. " in artist_text:
        return artist_text.split(" feat. ")[0].strip()
    elif " ft. " in artist_text:
        return artist_text.split(" ft. ")[0].strip()
    elif " & " in artist_text:
        return artist_text.split(" & ")[0].strip()
    elif " and " in artist_text.lower():
        return artist_text.split(" and ")[0].strip()
    
    return artist_text.strip()

def preprocess_lyrics_dict(lyrics_dict):
    """
    Preprocess lyrics dictionary to create additional formats for matching
    
    Args:
        lyrics_dict (dict): Dictionary of lyrics data
    
    Returns:
        tuple: (processed_dict, original_keys_map)
    """
    processed_dict = {}
    original_keys_map = {}  # Maps processed keys back to original keys
    
    for original_key, lyrics_text in lyrics_dict.items():
        if " - " not in original_key:
            continue
        
        try:
            artist, track = original_key.split(" - ", 1)
            
            # Clean up artist and track
            clean_artist = normalize_artist_name(artist)
            clean_track = clean_title(track)
            
            # Create multiple key variations for better matching
            key_variations = [
                f"{clean_track} by {clean_artist}",
                f"{clean_artist} {clean_track}",
                clean_track
            ]
            
            for key in key_variations:
                if key not in processed_dict:
                    processed_dict[key] = lyrics_text
                    original_keys_map[key] = original_key
        except Exception as e:
            print(f"Error processing key {original_key}: {e}")
    
    return processed_dict, original_keys_map

def find_matching_lyrics(track_title, artist_name, processed_lyrics_dict, original_keys_map, primary_artist_only=True):
    """
    Find matching lyrics for a track using fuzzy matching
    
    Args:
        track_title (str): The title of the track
        artist_name (str): The name of the artist
        processed_lyrics_dict (dict): Preprocessed dictionary of lyrics data
        original_keys_map (dict): Map from processed keys to original keys
        primary_artist_only (bool): Whether to use only the primary artist for matching
    
    Returns:
        tuple: (lyrics_found, lyrics_text, match_score, matched_key)
    """
    if not track_title:
        return False, None, 0, None
    
    # Clean and normalize the track title and artist name
    clean_track = clean_title(track_title)
    
    # Handle artist name - extract primary artist if needed
    if primary_artist_only and artist_name:
        artist_name = extract_first_artist(artist_name)
    
    clean_artist = normalize_artist_name(artist_name) if artist_name else ""
    
    # Create search queries based on track and artist
    search_queries = [
        f"{clean_track} by {clean_artist}" if clean_artist else clean_track,
        f"{clean_artist} {clean_track}" if clean_artist else clean_track,
        clean_track
    ]
    
    # Try direct key match first
    for query in search_queries:
        if query in processed_lyrics_dict:
            return True, processed_lyrics_dict[query], 100, original_keys_map[query]
    
    # If direct match fails, try fuzzy matching
    best_match = None
    best_score = 0
    best_lyrics = None
    matched_key = None
    
    # Try each search query with fuzzy matching
    for query in search_queries:
        # Skip empty queries
        if not query.strip():
            continue
        
        # Get the best matches using process.extractOne
        match = process.extractOne(
            query, 
            processed_lyrics_dict.keys(), 
            scorer=fuzz.token_sort_ratio,
            score_cutoff=70
        )
        
        if match and match[1] > best_score:
            matched_processed_key = match[0]
            best_score = match[1]
            best_lyrics = processed_lyrics_dict[matched_processed_key]
            matched_key = original_keys_map[matched_processed_key]
    
    # If we have a good match, return the lyrics
    if best_match or best_score >= 65:  # Lower threshold for fuzzy matching
        return True, best_lyrics, best_score, matched_key
    
    return False, None, 0, None

def match_tracks_to_lyrics(tracks_data, lyrics_dict):
    """
    Match tracks to lyrics using fuzzy matching
    
    Args:
        tracks_data (dict): Dictionary of track data
        lyrics_dict (dict): Dictionary of lyrics data
    
    Returns:
        dict: Dictionary mapping track keys to lyrics
    """
    # Preprocess lyrics dictionary for better matching
    processed_lyrics_dict, original_keys_map = preprocess_lyrics_dict(lyrics_dict)
    print(f"Preprocessed {len(processed_lyrics_dict)} unique keys for matching")
    
    # Map to store matches
    track_to_lyrics = {}
    match_stats = {
        'exact_matches': 0,
        'fuzzy_matches': 0,
        'no_matches': 0
    }
    
    match_confidence = {
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    # Process each track
    for key, data in tracks_data.items():
        track_name = data.get('track', '')
        if not track_name:
            continue
        
        # Get primary artist if available
        artist_name = ""
        if 'artist' in data and data['artist'] and isinstance(data['artist'], list) and len(data['artist']) > 0:
            if isinstance(data['artist'][0], dict) and 'artist_name' in data['artist'][0]:
                artist_name = data['artist'][0]['artist_name']
        
        # Try fuzzy matching
        found, lyrics_text, score, matched_key = find_matching_lyrics(
            track_name, artist_name, processed_lyrics_dict, original_keys_map
        )
        
        if found:
            track_to_lyrics[key] = lyrics_text
            if score >= 95:
                match_stats['exact_matches'] += 1
                match_confidence['high'] += 1
            elif score >= 80:
                match_stats['fuzzy_matches'] += 1
                match_confidence['medium'] += 1
            else:
                match_stats['fuzzy_matches'] += 1
                match_confidence['low'] += 1
        else:
            # Try again with different parameters
            found, lyrics_text, score, matched_key = find_matching_lyrics(
                track_name, artist_name, processed_lyrics_dict, original_keys_map, primary_artist_only=False
            )
            
            if found:
                track_to_lyrics[key] = lyrics_text
                if score >= 95:
                    match_stats['exact_matches'] += 1
                    match_confidence['high'] += 1
                elif score >= 80:
                    match_stats['fuzzy_matches'] += 1
                    match_confidence['medium'] += 1
                else:
                    match_stats['fuzzy_matches'] += 1
                    match_confidence['low'] += 1
            else:
                match_stats['no_matches'] += 1
    
    print(f"Matching stats: {match_stats['exact_matches']} exact matches, "
          f"{match_stats['fuzzy_matches']} fuzzy matches, "
          f"{match_stats['no_matches']} no matches")
    
    print(f"Match confidence: {match_confidence['high']} high, "
          f"{match_confidence['medium']} medium, "
          f"{match_confidence['low']} low")
    
    # If we still have a lot of no-matches, try a final round with very low thresholds
    # but only if more than 10% of tracks have no matches
    if match_stats['no_matches'] > len(tracks_data) * 0.1:
        print("Running final pass with lower thresholds for remaining tracks...")
        second_attempt_matches = 0
        
        for key, data in tracks_data.items():
            # Skip tracks that already have lyrics
            if key in track_to_lyrics:
                continue
                
            track_name = data.get('track', '')
            if not track_name:
                continue
            
            # Get primary artist if available
            artist_name = ""
            if 'artist' in data and data['artist'] and isinstance(data['artist'], list) and len(data['artist']) > 0:
                if isinstance(data['artist'][0], dict) and 'artist_name' in data['artist'][0]:
                    artist_name = data['artist'][0]['artist_name']
            
            # Just use the track name as is
            clean_track = clean_title(track_name)
            
            # Find the best possible match using just the clean track name
            match = process.extractOne(
                clean_track, 
                processed_lyrics_dict.keys(), 
                scorer=fuzz.token_sort_ratio,
                score_cutoff=50  # Very low threshold
            )
            
            if match:
                matched_processed_key = match[0]
                best_lyrics = processed_lyrics_dict[matched_processed_key]
                track_to_lyrics[key] = best_lyrics
                second_attempt_matches += 1
                match_confidence['low'] += 1
        
        print(f"Second pass found an additional {second_attempt_matches} matches")
    
    return track_to_lyrics 

def map_lyrics_to_track_ids(lyrics_dict, json_data, tracks_dict):
    """
    Map lyrics directly to track IDs from the mapping engine
    
    This function maps the lyrics data to track IDs that are already in the mapping engine,
    which ensures lyrics get properly attached to tracks in the knowledge graph.
    
    Args:
        lyrics_dict (dict): Dictionary mapping JSON keys to lyrics text
        json_data (dict): The original JSON data with track information
        tracks_dict (dict): Dictionary of track IDs from the mapping engine
    
    Returns:
        dict: Dictionary mapping track IDs to lyrics text
    """
    track_id_to_lyrics = {}
    key_to_track_id = {}
    mapped_count = 0
    
    # First, create a mapping from JSON keys to track IDs
    for json_key, data in json_data.items():
        track_name = data.get('track', '')
        artists = []
        
        if 'artist' in data and data['artist']:
            for artist_data in data['artist']:
                artist_name = artist_data.get('artist_name', '')
                if artist_name:
                    artists.append(artist_name)
        
        # Generate the track ID in the same way as the mapping engine
        primary_artist = artists[0] if artists else "unknown_artist"
        track_id = generate_entity_id(f"{track_name}_{primary_artist}")
        
        # Map JSON key to this track ID
        key_to_track_id[json_key] = track_id
    
    # Now map lyrics to track IDs if they exist in the tracks_dict
    for json_key, lyrics_text in lyrics_dict.items():
        if json_key in key_to_track_id:
            track_id = key_to_track_id[json_key]
            
            # Only map lyrics to tracks that exist in the mapping engine
            if track_id in tracks_dict:
                track_id_to_lyrics[track_id] = lyrics_text
                mapped_count += 1
    
    print(f"Mapped lyrics to {mapped_count} out of {len(lyrics_dict)} tracks that exist in the knowledge graph")
    
    return track_id_to_lyrics 

def match_csv_to_lyrics(csv_data, lyrics_dict):
    """
    Match tracks from CSV data directly to lyrics
    
    Args:
        csv_data (pandas.DataFrame): DataFrame containing CSV chart data
        lyrics_dict (dict): Dictionary of lyrics data
    
    Returns:
        dict: Dictionary mapping track IDs (as would be created from CSV) to lyrics
    """
    # Preprocess lyrics dictionary for better matching
    processed_lyrics_dict, original_keys_map = preprocess_lyrics_dict(lyrics_dict)
    print(f"Preprocessed {len(processed_lyrics_dict)} unique keys for matching")
    
    # Create a unique set of track-artist pairs from the CSV
    unique_tracks = {}
    for _, row in csv_data.iterrows():
        track_name = row['song']
        artist_name = row['artist']
        
        # Generate the same track ID that will be used in the mapping engine
        track_id = generate_entity_id(f"{track_name}_{artist_name}")
        
        # Only add each unique track once
        if track_id not in unique_tracks:
            unique_tracks[track_id] = (track_name, artist_name)
    
    print(f"Found {len(unique_tracks)} unique tracks in CSV data")
    
    # Map to store matches
    track_id_to_lyrics = {}
    match_stats = {
        'exact_matches': 0,
        'fuzzy_matches': 0,
        'no_matches': 0
    }
    
    match_confidence = {
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    # Process each unique track
    for track_id, (track_name, artist_name) in unique_tracks.items():
        # Try fuzzy matching
        found, lyrics_text, score, matched_key = find_matching_lyrics(
            track_name, artist_name, processed_lyrics_dict, original_keys_map
        )
        
        if found:
            track_id_to_lyrics[track_id] = lyrics_text
            if score >= 95:
                match_stats['exact_matches'] += 1
                match_confidence['high'] += 1
            elif score >= 80:
                match_stats['fuzzy_matches'] += 1
                match_confidence['medium'] += 1
            else:
                match_stats['fuzzy_matches'] += 1
                match_confidence['low'] += 1
        else:
            # Try again with different parameters
            found, lyrics_text, score, matched_key = find_matching_lyrics(
                track_name, artist_name, processed_lyrics_dict, original_keys_map, primary_artist_only=False
            )
            
            if found:
                track_id_to_lyrics[track_id] = lyrics_text
                if score >= 95:
                    match_stats['exact_matches'] += 1
                    match_confidence['high'] += 1
                elif score >= 80:
                    match_stats['fuzzy_matches'] += 1
                    match_confidence['medium'] += 1
                else:
                    match_stats['fuzzy_matches'] += 1
                    match_confidence['low'] += 1
            else:
                match_stats['no_matches'] += 1
    
    print(f"Matching stats: {match_stats['exact_matches']} exact matches, "
          f"{match_stats['fuzzy_matches']} fuzzy matches, "
          f"{match_stats['no_matches']} no matches")
    
    print(f"Match confidence: {match_confidence['high']} high, "
          f"{match_confidence['medium']} medium, "
          f"{match_confidence['low']} low")
    
    # If we still have a lot of no-matches, try a final round with very low thresholds
    # but only if more than 10% of tracks have no matches
    if match_stats['no_matches'] > len(unique_tracks) * 0.1:
        print("Running final pass with lower thresholds for remaining tracks...")
        second_attempt_matches = 0
        
        for track_id, (track_name, artist_name) in unique_tracks.items():
            # Skip tracks that already have lyrics
            if track_id in track_id_to_lyrics:
                continue
            
            # Just use the track name as is
            clean_track = clean_title(track_name)
            
            # Find the best possible match using just the clean track name
            match = process.extractOne(
                clean_track, 
                processed_lyrics_dict.keys(), 
                scorer=fuzz.token_sort_ratio,
                score_cutoff=50  # Very low threshold
            )
            
            if match:
                matched_processed_key = match[0]
                best_lyrics = processed_lyrics_dict[matched_processed_key]
                track_id_to_lyrics[track_id] = best_lyrics
                second_attempt_matches += 1
                match_confidence['low'] += 1
        
        print(f"Second pass found an additional {second_attempt_matches} matches")
    
    return track_id_to_lyrics 

def match_csv_to_enriched_lyrics(csv_data, lyrics_enriched_path):
    """
    Match tracks from CSV data directly to lyrics from lyrics_enriched.csv
    
    Args:
        csv_data (pandas.DataFrame): DataFrame containing chart data
        lyrics_enriched_path (str): Path to the lyrics_enriched.csv file
    
    Returns:
        dict: Dictionary mapping track IDs (as would be created from CSV) to enriched lyrics data
    """
    # Load the enriched lyrics data
    print(f"Loading enriched lyrics from {lyrics_enriched_path}...")
    lyrics_df = pd.read_csv(lyrics_enriched_path)
    print(f"Loaded {len(lyrics_df)} enriched lyrics entries")
    
    # Create a map of processed artist and track names for better matching
    processed_lyrics = {}
    for _, row in lyrics_df.iterrows():
        artist = row['artist']
        title = row['title']
        
        # Clean up artist and track
        clean_artist = normalize_artist_name(artist)
        clean_track = clean_title(title)
        
        # Create variations for better matching
        key_variations = [
            f"{clean_track} by {clean_artist}",
            f"{clean_artist} {clean_track}",
            clean_track
        ]
        
        # Store all variations with reference to the original row
        for key in key_variations:
            if key not in processed_lyrics:
                processed_lyrics[key] = row
    
    print(f"Processed {len(processed_lyrics)} unique keys for lyrics matching")
    
    # Create a unique set of track-artist pairs from the CSV
    unique_tracks = {}
    for _, row in csv_data.iterrows():
        track_name = row['song']
        artist_name = row['artist']
        
        # Generate the same track ID that will be used in the mapping engine
        track_id = generate_entity_id(f"{track_name}_{artist_name}")
        
        # Only add each unique track once
        if track_id not in unique_tracks:
            unique_tracks[track_id] = (track_name, artist_name)
    
    print(f"Found {len(unique_tracks)} unique tracks in CSV data")
    
    # Map to store matches
    track_id_to_lyrics = {}
    match_stats = {
        'exact_matches': 0,
        'fuzzy_matches': 0,
        'no_matches': 0
    }
    
    match_confidence = {
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    # Process each unique track
    for track_id, (track_name, artist_name) in unique_tracks.items():
        # Clean and normalize the track and artist
        clean_track = clean_title(track_name)
        clean_artist = normalize_artist_name(artist_name)
        
        # Create search queries
        search_queries = [
            f"{clean_track} by {clean_artist}",
            f"{clean_artist} {clean_track}",
            clean_track
        ]
        
        # Try direct match first
        match_found = False
        for query in search_queries:
            if query in processed_lyrics:
                lyrics_row = processed_lyrics[query]
                # Create a structured lyrics object with all enriched data
                lyrics_data = {
                    'lyrics': lyrics_row['cleaned_lyrics'],
                    'language': lyrics_row['detected_language'],
                    'translated': lyrics_row.get('translated_lyrics', ""),
                    'theme': lyrics_row.get('theme', "")
                }
                track_id_to_lyrics[track_id] = lyrics_data
                match_stats['exact_matches'] += 1
                match_confidence['high'] += 1
                match_found = True
                break
        
        # If no direct match, try fuzzy matching
        if not match_found:
            best_match = None
            best_score = 0
            
            for query in search_queries:
                if not query.strip():
                    continue
                
                # Find the best match using fuzzy matching
                match = process.extractOne(
                    query,
                    processed_lyrics.keys(),
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=70
                )
                
                if match and match[1] > best_score:
                    best_score = match[1]
                    best_match = match[0]
            
            if best_match:
                lyrics_row = processed_lyrics[best_match]
                # Create a structured lyrics object with all enriched data
                lyrics_data = {
                    'lyrics': lyrics_row['cleaned_lyrics'],
                    'language': lyrics_row['detected_language'],
                    'translated': lyrics_row.get('translated_lyrics', ""),
                    'theme': lyrics_row.get('theme', "")
                }
                track_id_to_lyrics[track_id] = lyrics_data
                
                if best_score >= 90:
                    match_stats['fuzzy_matches'] += 1
                    match_confidence['medium'] += 1
                else:
                    match_stats['fuzzy_matches'] += 1
                    match_confidence['low'] += 1
            else:
                match_stats['no_matches'] += 1
    
    print(f"Matching stats: {match_stats['exact_matches']} exact matches, "
          f"{match_stats['fuzzy_matches']} fuzzy matches, "
          f"{match_stats['no_matches']} no matches")
    
    print(f"Match confidence: {match_confidence['high']} high, "
          f"{match_confidence['medium']} medium, "
          f"{match_confidence['low']} low")
    
    # If we still have a lot of no-matches, try a final round with very low thresholds
    if match_stats['no_matches'] > len(unique_tracks) * 0.1:
        print("Running final pass with lower thresholds for remaining tracks...")
        second_attempt_matches = 0
        
        for track_id, (track_name, artist_name) in unique_tracks.items():
            # Skip tracks that already have lyrics
            if track_id in track_id_to_lyrics:
                continue
            
            # Just use the track name as is
            clean_track = clean_title(track_name)
            
            # Find the best possible match using just the clean track name
            match = process.extractOne(
                clean_track,
                processed_lyrics.keys(),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=50  # Very low threshold
            )
            
            if match:
                lyrics_row = processed_lyrics[match[0]]
                # Create a structured lyrics object with all enriched data
                lyrics_data = {
                    'lyrics': lyrics_row['cleaned_lyrics'],
                    'language': lyrics_row['detected_language'],
                    'translated': lyrics_row.get('translated_lyrics', ""),
                    'theme': lyrics_row.get('theme', "")
                }
                track_id_to_lyrics[track_id] = lyrics_data
                second_attempt_matches += 1
                match_confidence['low'] += 1
        
        print(f"Second pass found an additional {second_attempt_matches} matches")
    
    return track_id_to_lyrics 