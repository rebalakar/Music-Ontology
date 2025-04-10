import pandas as pd
import json
import re
import hashlib

def load_csv_data(file_path):
    """Load Billboard chart data from CSV file"""
    return pd.read_csv(file_path)

def load_json_data(file_path):
    """Load track information from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def clean_entity_name(name):
    """Clean entity names to use as IDs"""
    # Remove special characters and convert to lowercase
    cleaned = re.sub(r'[^\w\s]', '', name).lower().strip().replace(' ', '_')
    # Limit length to avoid excessively long IDs
    if len(cleaned) > 40:
        cleaned = cleaned[:40]
    return cleaned

def generate_entity_id(name):
    """Generate a unique ID for an entity based on its name"""
    # First, create a readable slug
    readable_id = clean_entity_name(name)
    
    # Add a short hash suffix (first 6 chars of MD5) to ensure uniqueness
    # This maintains uniqueness while still being mostly readable
    short_hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:6]
    
    # Return the combined readable ID with hash suffix
    return f"{readable_id}_{short_hash}"

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