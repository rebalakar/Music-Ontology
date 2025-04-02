# Mapping Engine

## Structure

```
project/
├── data/                      # Data files
├── ontologies/                # Ontology files
├── output/                    # Generated output
└── src/                       # Mapping scripts
    ├── config.py              # Configuration settings
    ├── data_loader.py         # Data loading utilities
    ├── entity_resolution.py   # Entity resolution functions
    ├── mapping_engine.py      # Core mapping functionality
    ├── main.py                # Main script to run the pipeline
    └── count_entities.py      # Entity counting utility
```

## Mapping Implementation

The mapping process involves several components:

1. **Configuration (`src/config.py`)**: Contains namespaces, file paths, and entity IRI patterns.
2. **Data Loading (`src/data_loader.py`)**: Functions to load and process data from different sources.
3. **Entity Resolution (`src/entity_resolution.py`)**: Handles fuzzy matching for entity resolution.
4. **Mapping Engine (`src/mapping_engine.py`)**: Core component that maps data to RDF triples.
5. **Main Script (`src/main.py`)**: Orchestrates the entire mapping process.

## Usage

### Prerequisites

- Python 3.6+
- Required packages (install via `pip install -r requirements.txt`):
  - rdflib
  - pandas
  - rapidfuzz
  - numpy

### How to run

Run the main script to generate the knowledge graph:

```bash
# Navigate to the src directory
cd src

# Run the main script
python main.py
```

This will:
1. Load data from CSV and JSON sources
2. Map the data to RDF triples
3. Save the resulting knowledge graph to `output/music_knowledge_graph.ttl`

To check the entity counts in the generated graph, run:

```bash
# In the src directory
python count_entities.py
```

## Mapping Approaches

### CSV Mapping

The CSV data is mapped as follows:
- Each row becomes a ChartEntry in the knowledge graph
- Songs are mapped to Track entities
- Artists are extracted and mapped to MusicArtist entities
- Dates are mapped to time:Instant entities
- Chart positions are mapped as chartPosition properties

### JSON Mapping

The JSON data is mapped as follows:
- Each object becomes additional properties for existing or new Track entities
- Artist details are added to existing or new MusicArtist entities
- Additional properties like language, writers, composers are added
- Tags are added as comments

### Entity Resolution

Entity resolution is handled through:
- Unique ID generation based on entity names
- Fuzzy matching for artist and track names
- Cross-referencing entities across different data sources

## Output

The output graph contains:
- Tracks with their associated artists, writers, languages, and other metadata
- Music artists with their gender, legal names, and relationships to tracks
- Chart entries linking tracks to chart positions and dates
- Time instants for the chart dates