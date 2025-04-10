import os
import sys
import time
import psutil

# Add the parent directory to sys.path to allow imports within src
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Simplified imports from the same directory
from data_loader import load_csv_data, load_json_data
from mapping_engine import MappingEngine
from config import CSV_DATA_PATH, JSON_DATA_PATH, OUTPUT_PATH
from lyrics_matcher import match_tracks_to_lyrics, map_lyrics_to_track_ids, match_csv_to_lyrics, match_csv_to_enriched_lyrics

# Define paths to lyrics data
LYRICS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'lyrics.json')
LYRICS_ENRICHED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'lyrics_enriched.csv')

def main():
    metrics = {}

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Load data
    print("Loading CSV data...")
    start_ingest_csv = time.time() 
    csv_data = load_csv_data(CSV_DATA_PATH)
    csv_ingest_time = time.time() - start_ingest_csv
    metrics["CSV Ingestion (s)"] = csv_ingest_time
    print(f"Loaded {len(csv_data)} chart entries in {csv_ingest_time:.2f} seconds")
    
    print("Loading JSON data...")
    start_ingest_json = time.time()
    json_data = load_json_data(JSON_DATA_PATH)
    json_ingest_time = time.time() - start_ingest_json
    metrics["JSON Ingestion (s)"] = json_ingest_time
    print(f"Loaded information for {len(json_data)} tracks in {json_ingest_time:.2f} seconds")
    
    # Load lyrics data - now using the enriched CSV instead of JSON
    track_id_to_lyrics = None
    if os.path.exists(LYRICS_ENRICHED_PATH):
        print("Using enriched lyrics data from CSV...")
        # Match lyrics directly to CSV data tracks using the enriched lyrics source
        print("Matching CSV tracks directly to enriched lyrics...")
        track_id_to_lyrics = match_csv_to_enriched_lyrics(csv_data, LYRICS_ENRICHED_PATH)
        print(f"Matched enriched lyrics to {len(track_id_to_lyrics)} unique tracks from CSV data")
    else:
        print(f"Enriched lyrics file not found at {LYRICS_ENRICHED_PATH}, trying regular lyrics.json")
        # Fall back to the original lyrics.json approach if needed
        if os.path.exists(LYRICS_JSON_PATH):
            print("Loading lyrics data from JSON...")
            lyrics_data = load_json_data(LYRICS_JSON_PATH)
            print(f"Loaded lyrics for {len(lyrics_data)} tracks")
            
            # Match lyrics directly to CSV data tracks
            print("Matching CSV tracks directly to lyrics...")
            track_id_to_lyrics = match_csv_to_lyrics(csv_data, lyrics_data)
            print(f"Matched lyrics to {len(track_id_to_lyrics)} unique tracks from CSV data")
        else:
            print(f"No lyrics file found, continuing without lyrics")
    
    # Record memory consumption before mapping
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss 
    print(f"Memory before mapping: {mem_before / 1e6:.2f} MB")

    # Initialize mapping engine
    print("Initializing mapping engine...")
    start_mapping = time.time()
    engine = MappingEngine()
    
    # Map CSV data to RDF first
    print("Mapping CSV data to RDF...")
    engine.map_csv_data(csv_data, track_id_to_lyrics)  # Pass lyrics directly to map_csv_data
    
    # Map JSON data to RDF (without lyrics - they're already attached in map_csv_data)
    print("Mapping JSON data to RDF...")
    engine.map_json_data(json_data)
    mapping_time = time.time() - start_mapping
    metrics["Mapping Engine (s)"] = mapping_time
    print(f"Mapping engine processing took {mapping_time:.2f} seconds")
    
    # Record memory consumption after mapping
    mem_after = process.memory_info().rss  
    mem_increase = (mem_after - mem_before) / 1e6  # Convert to MB
    metrics["Memory Increase (MB)"] = mem_increase
    print(f"Memory increased by {mem_increase:.2f} MB during mapping")

    # Save the resulting graph
    print("Saving knowledge graph...")
    engine.save_graph(OUTPUT_PATH)
    
    print("Mapping complete!")

    return metrics

if __name__ == "__main__":
    main() 