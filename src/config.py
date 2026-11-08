import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Namespaces and prefixes
NAMESPACES = {
    'mo': 'http://example.org/mo#',
    'ex': 'http://example.org/billboard#',
    'time': 'http://example.org/time#',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'owl': 'http://www.w3.org/2002/07/owl#'
}

# File paths 
CSV_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'singles_charts_2010s_cleaned.csv')
JSON_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'recordings.json')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'output', 'music_knowledge_graph.ttl')

# Entity IRI patterns
TRACK_IRI_PATTERN = 'http://example.org/mo#track_{}'
ARTIST_IRI_PATTERN = 'http://example.org/mo#artist_{}'
CHART_ENTRY_IRI_PATTERN = 'http://example.org/billboard#chartEntry_{}'
CHART_IRI_PATTERN = 'http://example.org/billboard#chart_{}'
TIME_INSTANT_IRI_PATTERN = 'http://example.org/time#instant_{}'
RECORD_IRI_PATTERN = 'http://example.org/mo#record_{}'
GENRE_IRI_PATTERN = 'http://example.org/mo#genre_{}'
LABEL_IRI_PATTERN = 'http://example.org/mo#label_{}'
WRITER_IRI_PATTERN = 'http://example.org/mo#writer_{}'
PRODUCER_IRI_PATTERN = 'http://example.org/mo#producer_{}'
ARRANGER_IRI_PATTERN = 'http://example.org/mo#arranger_{}'
TIME_INTERVAL_IRI_PATTERN = 'http://example.org/time#interval_{}'
TIME_DURATION_IRI_PATTERN = 'http://example.org/time#duration_{}'
TEMPORAL_UNIT_IRI_PATTERN = 'http://example.org/time#unit_{}'
CHART_RUN_IRI_PATTERN = 'http://example.org/billboard#chartRun_{}' 