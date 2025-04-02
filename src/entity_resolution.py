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