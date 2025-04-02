import os
import sys

# Add the parent directory to sys.path to allow imports within src
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Simplified imports from the same directory
from data_loader import load_csv_data, load_json_data
from mapping_engine import MappingEngine
from config import CSV_DATA_PATH, JSON_DATA_PATH, OUTPUT_PATH

def main():
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Load data
    print("Loading CSV data...")
    csv_data = load_csv_data(CSV_DATA_PATH)
    print(f"Loaded {len(csv_data)} chart entries")
    
    print("Loading JSON data...")
    json_data = load_json_data(JSON_DATA_PATH)
    print(f"Loaded information for {len(json_data)} tracks")
    
    # Initialize mapping engine
    print("Initializing mapping engine...")
    engine = MappingEngine()
    
    # Map data to RDF
    print("Mapping CSV data to RDF...")
    engine.map_csv_data(csv_data)
    
    print("Mapping JSON data to RDF...")
    engine.map_json_data(json_data)
    
    # Save the resulting graph
    print("Saving knowledge graph...")
    engine.save_graph(OUTPUT_PATH)
    
    print("Mapping complete!")

if __name__ == "__main__":
    main() 