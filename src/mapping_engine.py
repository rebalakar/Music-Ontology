import rdflib
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import pandas as pd
import os
import sys

# Add the current directory to sys.path for local imports
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Simplified imports from the same directory
from config import NAMESPACES, TRACK_IRI_PATTERN, ARTIST_IRI_PATTERN, CHART_ENTRY_IRI_PATTERN, CHART_IRI_PATTERN, TIME_INSTANT_IRI_PATTERN
from data_loader import clean_entity_name, generate_entity_id

class MappingEngine:
    def __init__(self):
        self.graph = Graph()
        # Register namespaces
        for prefix, uri in NAMESPACES.items():
            self.graph.bind(prefix, Namespace(uri))
        
        # Initialize namespaces for easier use
        self.mo = Namespace(NAMESPACES['mo'])
        self.ex = Namespace(NAMESPACES['ex'])
        self.time = Namespace(NAMESPACES['time'])
        
        # Track existing entities to avoid duplicates
        self.tracks = {}
        self.artists = {}
        self.instants = {}
        self.charts = {}
        self.genders = {}
        self.languages = {}
        
        # Initialize common entities
        self._initialize_common_entities()
    
    def _initialize_common_entities(self):
        """Initialize common entities like genders and languages"""
        # Create gender instances
        gender_instances = ["Male", "Female", "Other", "Unknown"]
        for gender in gender_instances:
            gender_id = gender.lower()
            gender_uri = URIRef(f"{NAMESPACES['mo']}gender_{gender_id}")
            self.genders[gender_id] = gender_uri
            self.graph.add((gender_uri, RDF.type, self.mo.Gender))
            self.graph.add((gender_uri, RDFS.label, Literal(gender, lang="en")))
        
        # Initialize language instances as needed
        language_codes = ["eng", "spa", "fra", "deu", "ita", "por"]
        language_names = ["English", "Spanish", "French", "German", "Italian", "Portuguese"]
        
        for code, name in zip(language_codes, language_names):
            language_uri = URIRef(f"{NAMESPACES['mo']}language_{code}")
            self.languages[code] = language_uri
            self.graph.add((language_uri, RDF.type, self.mo.Language))
            self.graph.add((language_uri, RDFS.label, Literal(name, lang="en")))
        
    def map_csv_data(self, df):
        """Map Billboard chart data from CSV to RDF triples"""
        
        # Create Billboard Hot 100 chart as a constant
        billboard_hot100 = URIRef(CHART_IRI_PATTERN.format('hot_100'))
        self.graph.add((billboard_hot100, RDF.type, self.ex.MusicChart))
        self.graph.add((billboard_hot100, RDFS.label, Literal("Billboard Hot 100", lang="en")))
        
        # Process each row in the CSV
        for _, row in df.iterrows():
            self._map_chart_entry(row)
    
    def _map_chart_entry(self, row):
        """Map a single chart entry from CSV row to RDF triples"""
        
        # Extract data from the row
        rank = row['rank']
        song_title = row['song']
        artist_name = row['artist']
        chart_date = row['date']
        
        # Generate IDs
        track_id = generate_entity_id(f"{song_title}_{artist_name}")
        chart_entry_id = generate_entity_id(f"{song_title}_{artist_name}_{chart_date}_{rank}")
        time_instant_id = chart_date
        
        # Create URIs
        track_uri = URIRef(TRACK_IRI_PATTERN.format(track_id))
        chart_entry_uri = URIRef(CHART_ENTRY_IRI_PATTERN.format(chart_entry_id))
        time_instant_uri = URIRef(TIME_INSTANT_IRI_PATTERN.format(time_instant_id))
        chart_uri = URIRef(CHART_IRI_PATTERN.format('hot_100'))
        
        # Add track if it doesn't exist
        if track_id not in self.tracks:
            self.tracks[track_id] = track_uri
            self.graph.add((track_uri, RDF.type, self.mo.Track))
            self.graph.add((track_uri, RDFS.label, Literal(song_title, lang="en")))
            
            # Process artist(s)
            self._process_artists(artist_name, track_uri)
        
        # Add time instant if it doesn't exist
        if time_instant_id not in self.instants:
            self.instants[time_instant_id] = time_instant_uri
            self.graph.add((time_instant_uri, RDF.type, self.time.Instant))
            self.graph.add((time_instant_uri, self.time.instantDate, Literal(chart_date, datatype=XSD.date)))
        
        # Create chart entry
        self.graph.add((chart_entry_uri, RDF.type, self.ex.ChartEntry))
        self.graph.add((chart_entry_uri, self.ex.chartPosition, Literal(rank, datatype=XSD.integer)))
        self.graph.add((chart_entry_uri, self.ex.chart, chart_uri))
        self.graph.add((chart_entry_uri, self.time.inDate, time_instant_uri))
        self.graph.add((chart_entry_uri, self.mo.forTrack, track_uri))
    
    def _process_artists(self, artist_text, track_uri):
        """Process artist field from CSV and create artist entities"""
        
        # Handle various forms of artist collaborations (feat., ft., &, etc.)
        artists = []
        if " feat. " in artist_text:
            artists = artist_text.split(" feat. ")
        elif " ft. " in artist_text:
            artists = artist_text.split(" ft. ")
        elif " & " in artist_text:
            artists = artist_text.split(" & ")
        else:
            artists = [artist_text]
        
        for artist_name in artists:
            artist_id = generate_entity_id(artist_name)
            artist_uri = URIRef(ARTIST_IRI_PATTERN.format(artist_id))
            
            if artist_id not in self.artists:
                self.artists[artist_id] = artist_uri
                self.graph.add((artist_uri, RDF.type, self.mo.MusicArtist))
                self.graph.add((artist_uri, RDFS.label, Literal(artist_name, lang="en")))
                
                # Default to unknown gender for artists from CSV
                gender_uri = self.genders.get("unknown")
                if gender_uri:
                    self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
            
            # Link track to artist
            self.graph.add((track_uri, self.mo.hasMusicArtist, artist_uri))
    
    def map_json_data(self, json_data):
        """Map track information from JSON to RDF triples"""
        
        for key, data in json_data.items():
            # Extract track name and process
            track_name = data.get('track', '')
            track_id = generate_entity_id(track_name)
            track_uri = URIRef(TRACK_IRI_PATTERN.format(track_id))
            
            # Check if track exists (might have been created from CSV)
            track_exists = False
            for existing_id, existing_uri in self.tracks.items():
                if track_name.lower() in existing_id.lower():
                    track_uri = existing_uri
                    track_exists = True
                    break
            
            if not track_exists:
                self.tracks[track_id] = track_uri
                self.graph.add((track_uri, RDF.type, self.mo.Track))
                self.graph.add((track_uri, RDFS.label, Literal(track_name, lang="en")))
            
            # Process language
            if 'language' in data and data['language']:
                language_code = data['language']
                language_uri = self.languages.get(language_code)
                
                if not language_uri:
                    # Create a new language if not in our predefined list
                    language_uri = URIRef(f"{NAMESPACES['mo']}language_{language_code}")
                    self.languages[language_code] = language_uri
                    self.graph.add((language_uri, RDF.type, self.mo.Language))
                    self.graph.add((language_uri, RDFS.label, Literal(language_code, lang="en")))
                
                self.graph.add((track_uri, self.mo.hasLanguage, language_uri))
            
            # Process artists
            if 'artist' in data and data['artist']:
                for artist_data in data['artist']:
                    artist_name = artist_data.get('artist_name', '')
                    if not artist_name:
                        continue
                    
                    artist_id = generate_entity_id(artist_name)
                    artist_uri = URIRef(ARTIST_IRI_PATTERN.format(artist_id))
                    
                    if artist_id not in self.artists:
                        self.artists[artist_id] = artist_uri
                        self.graph.add((artist_uri, RDF.type, self.mo.MusicArtist))
                        self.graph.add((artist_uri, RDFS.label, Literal(artist_name, lang="en")))
                        
                        # Process gender if available
                        if 'gender' in artist_data and artist_data['gender']:
                            gender = artist_data['gender'].lower()
                            gender_uri = self.genders.get(gender.lower())
                            
                            if gender_uri:
                                self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
                        else:
                            # Default to unknown gender
                            gender_uri = self.genders.get("unknown")
                            if gender_uri:
                                self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
                        
                        # Process legal names if available
                        if 'legal_name' in artist_data and artist_data['legal_name']:
                            for legal_name in artist_data['legal_name']:
                                if legal_name:  # Check if not empty
                                    self.graph.add((artist_uri, self.mo.hasLegalName, Literal(legal_name)))
                    
                    # Link track to artist
                    self.graph.add((track_uri, self.mo.hasMusicArtist, artist_uri))
            
            # Process writers
            if 'writer' in data and data['writer']:
                for writer_name in data['writer']:
                    if not writer_name:
                        continue
                    
                    writer_id = generate_entity_id(writer_name)
                    writer_uri = URIRef(f"{NAMESPACES['mo']}writer_{writer_id}")
                    
                    self.graph.add((writer_uri, RDF.type, self.mo.MusicWriter))
                    self.graph.add((writer_uri, RDFS.label, Literal(writer_name, lang="en")))
                    self.graph.add((track_uri, self.mo.hasWriter, writer_uri))
            
            # Process composers if available
            if 'composer' in data and data['composer']:
                for composer_name in data['composer']:
                    if not composer_name:
                        continue
                    
                    composer_id = generate_entity_id(composer_name)
                    composer_uri = URIRef(f"{NAMESPACES['mo']}composer_{composer_id}")
                    
                    self.graph.add((composer_uri, RDF.type, self.mo.MusicProducer))
                    self.graph.add((composer_uri, RDFS.label, Literal(composer_name, lang="en")))
                    self.graph.add((track_uri, self.mo.hasProducer, composer_uri))
            
            # Process tags if available
            if 'tags' in data and data['tags']:
                for tag in data['tags']:
                    if not tag:
                        continue
                    
                    # Add tag as a literal property
                    self.graph.add((track_uri, RDFS.comment, Literal(f"Tag: {tag}", lang="en")))
    
    def save_graph(self, output_path):
        """Save the graph to a Turtle file"""
        self.graph.serialize(destination=output_path, format='turtle')
        print(f"Knowledge graph saved to {output_path} with {len(self.graph)} triples") 