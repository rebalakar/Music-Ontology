import os
import sys
import json
import pandas as pd
import re
from collections import Counter, defaultdict
import pprint

# Add the parent directory to sys.path to allow imports within src
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Import configuration
from config import CSV_DATA_PATH, JSON_DATA_PATH

def extract_artists_from_text(artist_text):
    """
    Extract individual artists from a text containing multiple artists
    
    Args:
        artist_text (str): Text containing artist names, possibly with
                          features, collaborations, etc.
    
    Returns:
        list: List of individual artist names
    """
    artists = []
    
    # Handle "featuring" cases
    if " feat. " in artist_text:
        parts = artist_text.split(" feat. ")
        artists.append(parts[0].strip())
        # Handle multiple artists in the featuring part
        featured = parts[1].strip()
        if " & " in featured:
            artists.extend([a.strip() for a in featured.split(" & ")])
        elif " and " in featured.lower():
            artists.extend([a.strip() for a in featured.split(" and ")])
        elif "," in featured:
            artists.extend([a.strip() for a in featured.split(",")])
        else:
            artists.append(featured)
    
    # Handle "ft." cases
    elif " ft. " in artist_text:
        parts = artist_text.split(" ft. ")
        artists.append(parts[0].strip())
        # Handle multiple artists in the featuring part
        featured = parts[1].strip()
        if " & " in featured:
            artists.extend([a.strip() for a in featured.split(" & ")])
        elif " and " in featured.lower():
            artists.extend([a.strip() for a in featured.split(" and ")])
        elif "," in featured:
            artists.extend([a.strip() for a in featured.split(",")])
        else:
            artists.append(featured)
    
    # Handle ampersand cases
    elif " & " in artist_text:
        artists.extend([a.strip() for a in artist_text.split(" & ")])
    
    # Handle "and" cases
    elif " and " in artist_text.lower():
        artists.extend([a.strip() for a in artist_text.split(" and ")])
    
    # Handle comma-separated cases
    elif "," in artist_text and " feat" not in artist_text.lower() and " ft" not in artist_text.lower():
        artists.extend([a.strip() for a in artist_text.split(",")])
    
    # Single artist
    else:
        artists.append(artist_text.strip())
    
    # Clean up artist names
    cleaned_artists = []
    for artist in artists:
        # Remove text in parentheses
        artist = re.sub(r'\([^)]*\)', '', artist)
        # Remove any remaining featuring text
        artist = re.sub(r'(?i)\s+feat\..*$', '', artist)
        artist = re.sub(r'(?i)\s+ft\..*$', '', artist)
        # Clean up spaces
        artist = artist.strip()
        if artist:  # Only add non-empty artist names
            cleaned_artists.append(artist)
    
    return cleaned_artists

def analyze_csv_data(csv_path):
    """
    Analyze CSV data to get statistics
    
    Args:
        csv_path (str): Path to the CSV file
    
    Returns:
        dict: Dictionary containing statistics about the CSV data
    """
    print(f"Analyzing CSV data from {csv_path}...")
    
    # Load CSV data
    try:
        df = pd.read_csv(csv_path, header=None, names=['rank', 'song', 'artist', 'date'])
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        return {}
    
    # Count unique song titles
    unique_songs = df['song'].nunique()
    
    # Count unique dates
    unique_dates = df['date'].nunique()
    
    # Process artists to handle collaborations
    all_artists = []
    for artist_text in df['artist'].dropna():
        artists = extract_artists_from_text(artist_text)
        all_artists.extend(artists)
    
    # Count unique artists
    unique_artists = len(set(all_artists))
    
    # Get top artists by frequency
    artist_counts = Counter(all_artists)
    top_artists = artist_counts.most_common(10)
    
    # Get top songs by frequency
    song_counts = Counter(df['song'])
    top_songs = song_counts.most_common(10)
    
    # Create a combined song+artist field to identify unique tracks
    df['track_id'] = df['song'] + ' - ' + df['artist']
    unique_tracks = df['track_id'].nunique()
    
    return {
        'total_entries': len(df),
        'unique_songs': unique_songs,
        'unique_artists': unique_artists,
        'unique_dates': unique_dates,
        'unique_tracks': unique_tracks,
        'top_artists': top_artists,
        'top_songs': top_songs
    }

def analyze_json_data(json_path):
    """
    Analyze JSON data to get statistics from formatted_recordings.json
    
    Args:
        json_path (str): Path to the JSON file
    
    Returns:
        dict: Dictionary containing statistics about the JSON data
    """
    print(f"Analyzing JSON data from {json_path}...")
    
    # Load JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return {}
    
    # Display structure of first item for debugging
    try:
        first_key = next(iter(data))
        print("Example JSON entry structure:")
        pprint.pprint({first_key: data[first_key]}, depth=2, width=100)
    except:
        print("Could not display example JSON structure")
    
    # Count total number of entries
    total_entries = len(data)
    
    # Initialize counters for properties
    property_counts = defaultdict(set)  # For unique values
    property_instances = defaultdict(int)  # For total instances
    array_property_values = defaultdict(list)  # For collecting values in arrays
    
    # For tracking artist-related information
    all_artists = []
    artist_properties = defaultdict(list)
    
    # Track with key information
    track_analysis = {
        "keys_with_artists": 0,
        "total_artists_in_keys": 0,
        "keys_with_track_field": 0
    }
    
    # For field existence tracking (how many entries have each field)
    field_existence = defaultdict(int)
    
    # Process each entry
    for key, entry in data.items():
        # Analyze the key structure - often contains track/artist info
        if " - " in key:
            parts = key.split(" - ", 1)
            if len(parts) == 2:
                track_title = parts[0].strip()
                property_counts["key_track_title"].add(track_title)
                
                # Check if the artist part is in a format like ['Artist1', 'Artist2']
                artist_part = parts[1].strip()
                if artist_part.startswith("[") and artist_part.endswith("]"):
                    track_analysis["keys_with_artists"] += 1
                    # Try to parse as a Python list
                    try:
                        artists_in_key = eval(artist_part)
                        if isinstance(artists_in_key, list):
                            track_analysis["total_artists_in_keys"] += len(artists_in_key)
                            for artist in artists_in_key:
                                property_counts["key_artist_name"].add(artist)
                    except:
                        # If parsing fails, just store as a string
                        property_counts["key_artist_text"].add(artist_part)
        
        # Count which fields exist in each entry
        for field in entry:
            field_existence[field] += 1
        
        # Process each field in the entry
        for field, value in entry.items():
            # Track field has the track name
            if field == "track":
                track_analysis["keys_with_track_field"] += 1
                if value:  # Only add non-empty values
                    property_counts["track"].add(str(value))
                    property_instances["track"] += 1
            
            # Handle artist field specially - it contains nested objects
            elif field == "artist" and isinstance(value, list):
                for artist_obj in value:
                    if isinstance(artist_obj, dict):
                        all_artists.append(artist_obj)
                        
                        # Process artist name
                        artist_name = artist_obj.get("artist_name", "")
                        if artist_name:
                            property_counts["artist_name"].add(artist_name)
                            property_instances["artist_name"] += 1
                        
                        # Process all other artist properties
                        for artist_prop, prop_value in artist_obj.items():
                            if artist_prop == "legal_name" and isinstance(prop_value, list):
                                # Handle legal_name array
                                for legal_name in prop_value:
                                    if legal_name:
                                        artist_properties["legal_name"].append(legal_name)
                                        property_counts["legal_name"].add(legal_name)
                                        property_instances["legal_name"] += 1
                            elif artist_prop == "gender" and prop_value:
                                # Handle gender field
                                artist_properties["gender"].append(str(prop_value))
                                property_counts["gender"].add(str(prop_value))
                                property_instances["gender"] += 1
                            elif prop_value:  # Handle any other fields
                                field_name = f"artist_{artist_prop}"
                                if isinstance(prop_value, list):
                                    for item in prop_value:
                                        if item:
                                            artist_properties[artist_prop].append(str(item))
                                            property_counts[field_name].add(str(item))
                                            property_instances[field_name] += 1
                                else:
                                    artist_properties[artist_prop].append(str(prop_value))
                                    property_counts[field_name].add(str(prop_value))
                                    property_instances[field_name] += 1
            
            # Handle array fields - collect all values
            elif isinstance(value, list):
                for item in value:
                    if item:  # Only count non-empty values
                        array_property_values[field].append(str(item))
                        property_counts[field].add(str(item))
                        property_instances[field] += 1
            
            # Handle scalar fields
            elif value:  # Only count non-empty values
                property_counts[field].add(str(value))
                property_instances[field] += 1
    
    # Prepare the results
    results = {
        'total_entries': total_entries,
        'field_existence': dict(field_existence),
        'track_analysis': track_analysis,
        'total_artists': len(all_artists),
    }
    
    # Add property count statistics
    for prop, values in property_counts.items():
        results[f'unique_{prop}'] = len(values)
        results[f'total_{prop}_instances'] = property_instances.get(prop, 0)
    
    # Add statistics for array properties
    for prop, values in array_property_values.items():
        # Count total occurrences of each value
        value_counts = Counter(values)
        results[f'top_{prop}'] = value_counts.most_common(10)
    
    # Generate artist property statistics
    for prop, values in artist_properties.items():
        if values:
            value_counts = Counter(values)
            results[f'top_artist_{prop}'] = value_counts.most_common(10)
    
    return results

def generate_report(csv_stats, json_stats):
    """
    Generate a markdown report from the statistics
    
    Args:
        csv_stats (dict): Statistics from CSV data
        json_stats (dict): Statistics from JSON data
    
    Returns:
        str: Markdown-formatted report
    """
    report = "# Data Source Analysis Report\n\n"
    
    # CSV Statistics
    report += "## Billboard Chart Data (CSV)\n\n"
    report += f"- Total Chart Entries: {csv_stats.get('total_entries', 'N/A')}\n"
    report += f"- Unique Songs: {csv_stats.get('unique_songs', 'N/A')}\n"
    report += f"- Unique Artists: {csv_stats.get('unique_artists', 'N/A')}\n"
    report += f"- Unique Dates: {csv_stats.get('unique_dates', 'N/A')}\n"
    report += f"- Unique Tracks (Song + Artist combinations): {csv_stats.get('unique_tracks', 'N/A')}\n\n"
    
    # Top artists
    report += "### Top 10 Artists by Chart Appearances\n\n"
    report += "| Artist | Chart Appearances |\n"
    report += "|--------|-------------------|\n"
    for artist, count in csv_stats.get('top_artists', []):
        report += f"| {artist} | {count} |\n"
    report += "\n"
    
    # Top songs
    report += "### Top 10 Songs by Chart Appearances\n\n"
    report += "| Song | Chart Appearances |\n"
    report += "|------|-------------------|\n"
    for song, count in csv_stats.get('top_songs', []):
        report += f"| {song} | {count} |\n"
    report += "\n"
    
    # JSON Statistics
    report += "## Formatted Recordings Data (JSON)\n\n"
    report += f"- Total Entries: {json_stats.get('total_entries', 'N/A')}\n"
    report += f"- Total Artists: {json_stats.get('total_artists', 'N/A')}\n"
    
    # Field existence information
    if 'field_existence' in json_stats:
        report += "\n### Field Existence in Entries\n\n"
        report += "| Field | Present in # Entries | % of Entries |\n"
        report += "|-------|----------------------|-------------|\n"
        total_entries = json_stats.get('total_entries', 0)
        
        # Sort fields by frequency
        field_existence = json_stats['field_existence']
        sorted_fields = sorted(field_existence.items(), key=lambda x: x[1], reverse=True)
        
        for field, count in sorted_fields:
            percentage = (count / total_entries * 100) if total_entries > 0 else 0
            report += f"| {field} | {count} | {percentage:.2f}% |\n"
    
    # Track analysis information
    if 'track_analysis' in json_stats:
        track_analysis = json_stats['track_analysis']
        report += "\n### Key Structure Analysis\n\n"
        report += f"- Keys with Artists: {track_analysis.get('keys_with_artists', 'N/A')}\n"
        report += f"- Total Artists in Keys: {track_analysis.get('total_artists_in_keys', 'N/A')}\n"
        report += f"- Keys with Track Field: {track_analysis.get('keys_with_track_field', 'N/A')}\n"
    
    # Property statistics
    report += "\n### Property Statistics\n\n"
    report += "| Property | Unique Values | Total Instances |\n"
    report += "|----------|---------------|----------------|\n"
    
    # Get all properties with unique value counts
    unique_props = sorted([prop for prop in json_stats.keys() if prop.startswith('unique_')])
    
    for prop in unique_props:
        prop_name = prop.replace('unique_', '')
        unique_values = json_stats.get(prop, 'N/A')
        total_instances = json_stats.get(f'total_{prop_name}_instances', 'N/A')
        
        # Only include properties with actual data
        if unique_values != 'N/A' and unique_values > 0:
            report += f"| {prop_name} | {unique_values} | {total_instances} |\n"
    
    # Top values for array properties
    for prop in json_stats.keys():
        if prop.startswith('top_') and not prop.startswith('top_artist_'):
            prop_name = prop.replace('top_', '')
            
            if json_stats[prop]:
                report += f"\n### Top 10 {prop_name.capitalize()} Values\n\n"
                report += f"| {prop_name.capitalize()} | Count |\n"
                report += "|----------|-------|\n"
                for value, count in json_stats[prop]:
                    # Truncate long values
                    display_value = value if len(value) < 50 else value[:47] + "..."
                    report += f"| {display_value} | {count} |\n"
    
    # Artist-specific property statistics
    artist_props = sorted([prop for prop in json_stats.keys() if prop.startswith('top_artist_')])
    
    if artist_props:
        report += "\n## Artist-Specific Statistics\n\n"
        
        for prop in artist_props:
            prop_name = prop.replace('top_artist_', '')
            
            if json_stats[prop]:
                report += f"\n### Top 10 Artist {prop_name.capitalize()} Values\n\n"
                report += f"| {prop_name.capitalize()} | Count |\n"
                report += "|----------|-------|\n"
                for value, count in json_stats[prop]:
                    # Truncate long values
                    display_value = value if len(value) < 50 else value[:47] + "..."
                    report += f"| {display_value} | {count} |\n"
    
    return report

def main():
    """
    Main function to analyze data sources and generate a report
    """
    # Analyze CSV data
    csv_stats = analyze_csv_data(CSV_DATA_PATH)
    
    # Analyze JSON data
    json_stats = analyze_json_data(JSON_DATA_PATH)
    
    # Generate and save the report
    report = generate_report(csv_stats, json_stats)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save report to output directory
    report_path = os.path.join(output_dir, 'data_source_analysis.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Analysis complete! Report saved to {report_path}")
    
    # Print summary to console
    print("\nSummary of Findings:")
    print(f"CSV: {csv_stats.get('total_entries', 'N/A')} chart entries, {csv_stats.get('unique_songs', 'N/A')} unique songs, {csv_stats.get('unique_artists', 'N/A')} unique artists")
    print(f"JSON: {json_stats.get('total_entries', 'N/A')} entries, {json_stats.get('total_artists', 'N/A')} total artists")

if __name__ == "__main__":
    main() 