import re
import pandas as pd
from rapidfuzz import fuzz

def normalize_name(name):
    """Normalize names for comparison"""
    if pd.isna(name) or not isinstance(name, str):
        return ""
    return name.lower().strip()

def normalize_title(title):
    """Normalize track titles for comparison"""
    if pd.isna(title) or not isinstance(title, str):
        return ""
    # Remove common patterns like "feat.", parentheses content, etc.
    title = re.sub(r'\(.*?\)', '', title)
    title = re.sub(r'feat\..*', '', title)
    title = re.sub(r'ft\..*', '', title)
    return title.lower().strip()

def get_best_match(target, candidates, threshold=80):
    """Get the best matching string from a list of candidates using fuzzy matching"""
    if not target or not candidates:
        return None
    
    normalized_target = normalize_name(target)
    
    best_score = 0
    best_match = None
    
    for candidate in candidates:
        normalized_candidate = normalize_name(candidate)
        # Calculate similarity score
        score = fuzz.ratio(normalized_target, normalized_candidate)
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
    
    return best_match 

def find_matching_artist(artist_name, artist_id, existing_artists, threshold=75):
    """
    Find a matching artist in the existing artists dictionary
    
    Parameters:
    - artist_name: The name of the artist to find
    - artist_id: The generated ID for this artist
    - existing_artists: Dictionary of existing artist IDs to URIs
    - threshold: Similarity threshold for fuzzy matching (default: 75)
    
    Returns:
    - (match_found, artist_uri, matched_id): 
        match_found: Boolean indicating if a match was found
        artist_uri: The URI of the matched artist or the original one if no match
        matched_id: The ID of the matched artist (for tracking purposes)
    """
    # First check if this exact ID exists
    if artist_id in existing_artists:
        return True, existing_artists[artist_id], artist_id
    
    # Normalize the artist name for comparison
    normalized_name = normalize_name(artist_name)
    
    # First try direct substring matching (faster than fuzzy matching)
    for existing_id, existing_uri in existing_artists.items():
        existing_name = existing_id.split('_')[:-1]  # Remove the hash part
        existing_name = '_'.join(existing_name)
        
        # Check for simple contains relationship
        if normalized_name in existing_name or existing_name in normalized_name:
            return True, existing_uri, existing_id
    
    # If no direct match, try fuzzy matching with all existing artists
    candidates = []
    for existing_id in existing_artists.keys():
        existing_name = existing_id.split('_')[:-1]  # Remove the hash part
        existing_name = '_'.join(existing_name)
        existing_name = existing_name.replace('_', ' ')  # Convert back to spaces for comparison
        candidates.append((existing_id, existing_name))
    
    # Use fuzzy matching to find the best match
    best_score = 0
    best_match_id = None
    
    for candidate_id, candidate_name in candidates:
        score = fuzz.ratio(normalized_name, candidate_name)
        if score > best_score and score >= threshold:
            best_score = score
            best_match_id = candidate_id
    
    if best_match_id:
        return True, existing_artists[best_match_id], best_match_id
    
    # No match found
    return False, None, None 