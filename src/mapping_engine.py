import rdflib
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, XSD, OWL
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import re
from fuzzywuzzy import fuzz

# Add the current directory to sys.path for local imports
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Simplified imports from the same directory
from config import (
    NAMESPACES, TRACK_IRI_PATTERN, ARTIST_IRI_PATTERN, CHART_ENTRY_IRI_PATTERN, 
    CHART_IRI_PATTERN, TIME_INSTANT_IRI_PATTERN, RECORD_IRI_PATTERN, GENRE_IRI_PATTERN, 
    LABEL_IRI_PATTERN, WRITER_IRI_PATTERN, PRODUCER_IRI_PATTERN, ARRANGER_IRI_PATTERN,
    TIME_INTERVAL_IRI_PATTERN, TIME_DURATION_IRI_PATTERN, TEMPORAL_UNIT_IRI_PATTERN,
    CHART_RUN_IRI_PATTERN
)
from data_loader import clean_entity_name, generate_entity_id
from entity_resolution import find_matching_artist

class MappingEngine:
    def __init__(self, ontology_dir="ontologies"):
        self.graph = Graph()
        
        # Register namespaces
        for prefix, uri in NAMESPACES.items():
            self.graph.bind(prefix, Namespace(uri))
        
        # Initialize namespaces for easier use
        self.mo = Namespace(NAMESPACES['mo'])
        self.ex = Namespace(NAMESPACES['ex'])
        self.time = Namespace(NAMESPACES['time'])
        
        # Load the ontology files
        ontology_files = {
            "music": os.path.join(ontology_dir, "music_ontology.ttl"),
            "billboard": os.path.join(ontology_dir, "billboard.ttl"),
            "time": os.path.join(ontology_dir, "time.ttl")
        }
        
        # Load each ontology file into the graph
        for ont_file in ontology_files.values():
            if os.path.exists(ont_file):
                self.graph.parse(ont_file, format="turtle")
                print(f"Loaded ontology file: {ont_file}")
            else:
                print(f"Warning: Ontology file not found: {ont_file}")
        
        # Track existing entities to avoid duplicates
        self.tracks = {}
        self.artists = {}
        self.instants = {}
        self.charts = {}
        self.genders = {}
        self.languages = {}
        self.genres = {}
        self.records = {}
        self.labels = {}
        self.writers = {}
        self.producers = {}
        self.arrangers = {}
        self.intervals = {}
        self.durations = {}
        self.temporal_units = {}
        # Add new dictionaries for the additional roles
        self.engineers = {}
        self.mixers = {}
        self.vocalists = {}
        self.instrumentalists = {}
        self.recorders = {}
        # Track chart runs for each track (multiple runs per track possible)
        self.track_chart_runs = {}
        # Track chart entries by track and date for easier references
        self.track_chart_entries = {}
        
        # Initialize common entities (but don't redeclare ontology classes)
        self._initialize_common_entities()
    
    def _initialize_common_entities(self):
        """Initialize common entities for various ontology classes"""
        # Create gender instances
        gender_instances = ["Male", "Female", "Other", "Unknown"]
        for gender in gender_instances:
            gender_id = gender.lower()
            gender_uri = URIRef(f"{NAMESPACES['mo']}gender_{gender_id}")
            self.genders[gender_id] = gender_uri
            self.graph.add((gender_uri, RDF.type, self.mo.Gender))
            self.graph.add((gender_uri, RDFS.label, Literal(gender, lang="en")))
            self.graph.add((gender_uri, RDFS.comment, Literal(f"Represents {gender.lower()} gender.", lang="en")))
        
        # Initialize language instances
        language_codes = ["eng", "spa", "fra", "deu", "ita", "por", "mul"]
        language_names = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Multiple Languages"]
        
        for code, name in zip(language_codes, language_names):
            language_uri = URIRef(f"{NAMESPACES['mo']}language_{code}")
            self.languages[code] = language_uri
            self.graph.add((language_uri, RDF.type, self.mo.Language))
            self.graph.add((language_uri, RDFS.label, Literal(name, lang="en")))
            self.graph.add((language_uri, RDFS.comment, Literal(f"Represents the {name} language.", lang="en")))
        
        # Initialize common genres
        common_genres = ["Pop", "Rock", "Hip Hop", "R&B", "Country", "Electronic", "Jazz", "Classical", "Other"]
        for genre in common_genres:
            genre_id = clean_entity_name(genre)
            genre_uri = URIRef(GENRE_IRI_PATTERN.format(genre_id))
            self.genres[genre_id] = genre_uri
            self.graph.add((genre_uri, RDF.type, self.mo.Genre))
            self.graph.add((genre_uri, RDFS.label, Literal(genre, lang="en")))
            self.graph.add((genre_uri, RDFS.comment, Literal(f"Represents the {genre} music genre.", lang="en")))
        
        # Initialize temporal units
        units = ["second", "minute", "hour", "day", "week", "month", "year"]
        for unit in units:
            unit_uri = URIRef(TEMPORAL_UNIT_IRI_PATTERN.format(unit))
            self.temporal_units[unit] = unit_uri
            self.graph.add((unit_uri, RDF.type, self.time.TemporalUnit))
            self.graph.add((unit_uri, RDFS.label, Literal(unit, lang="en")))
            self.graph.add((unit_uri, RDFS.comment, Literal(f"Represents a time unit of one {unit}.", lang="en")))
        
        # Initialize Billboard Hot 100 chart
        billboard_hot100 = URIRef(CHART_IRI_PATTERN.format('hot_100'))
        self.charts['hot_100'] = billboard_hot100
        self.graph.add((billboard_hot100, RDF.type, self.ex.MusicChart))
        self.graph.add((billboard_hot100, RDFS.label, Literal("Billboard Hot 100", lang="en")))
        self.graph.add((billboard_hot100, RDFS.comment, Literal("The Billboard Hot 100 music chart that ranks the most popular songs in the United States.", lang="en")))
    
    def map_csv_data(self, df, lyrics_dict=None):
        """
        Map Billboard chart data from CSV to RDF triples
        
        Args:
            df (pandas.DataFrame): DataFrame containing chart data
            lyrics_dict (dict, optional): Dictionary mapping track IDs to lyrics
        """
        # Store lyrics data for later use if provided
        self.lyrics_dict = lyrics_dict or {}
        
        # Process each row in the CSV
        for _, row in df.iterrows():
            self._map_chart_entry(row)
    
    def _create_time_interval(self, start_date_str, duration_days=7):
        """Create a time interval with start date and duration"""
        
        # Parse the start date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = start_date + timedelta(days=duration_days)
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Generate IDs for components
        interval_id = f"{start_date_str}_to_{end_date_str}"
        duration_id = f"{duration_days}_days"
        
        # Create or retrieve time instant for start date
        start_instant_uri = self._get_or_create_time_instant(start_date_str)
        
        # Create or retrieve time instant for end date
        end_instant_uri = self._get_or_create_time_instant(end_date_str)
        
        # Create or retrieve duration
        duration_uri = self._get_or_create_duration(duration_days, "day")
        
        # Create or retrieve interval
        if interval_id in self.intervals:
            return self.intervals[interval_id]
        
        interval_uri = URIRef(TIME_INTERVAL_IRI_PATTERN.format(interval_id))
        self.intervals[interval_id] = interval_uri
        
        # Add interval properties
        self.graph.add((interval_uri, RDF.type, self.time.Interval))
        self.graph.add((interval_uri, RDFS.label, Literal(f"Week of {start_date_str}", lang="en")))
        self.graph.add((interval_uri, RDFS.comment, Literal(f"Time interval from {start_date_str} to {end_date_str}.", lang="en")))
        self.graph.add((interval_uri, self.time.hasBeginning, start_instant_uri))
        self.graph.add((interval_uri, self.time.hasEnd, end_instant_uri))
        
        return interval_uri
    
    def _get_or_create_time_instant(self, date_str):
        """Get or create a time instant for a given date"""
        
        if date_str in self.instants:
            return self.instants[date_str]
        
        instant_uri = URIRef(TIME_INSTANT_IRI_PATTERN.format(date_str))
        self.instants[date_str] = instant_uri
        
        self.graph.add((instant_uri, RDF.type, self.time.Instant))
        self.graph.add((instant_uri, RDFS.label, Literal(f"Time instant {date_str}", lang="en")))
        self.graph.add((instant_uri, RDFS.comment, Literal(f"A specific point in time on date {date_str}.", lang="en")))
        self.graph.add((instant_uri, self.time.instantDate, Literal(date_str, datatype=XSD.date)))
        
        return instant_uri
    
    def _get_or_create_duration(self, amount, unit):
        """Get or create a duration with a specific amount and unit"""
        
        # Ensure amount is positive
        amount = abs(amount)
        
        duration_id = f"{amount}_{unit}"
        if duration_id in self.durations:
            return self.durations[duration_id]
        
        duration_uri = URIRef(TIME_DURATION_IRI_PATTERN.format(duration_id))
        self.durations[duration_id] = duration_uri
        
        # Get or create the unit
        unit_uri = self.temporal_units.get(unit)
        if not unit_uri:
            unit_uri = URIRef(TEMPORAL_UNIT_IRI_PATTERN.format(unit))
            self.temporal_units[unit] = unit_uri
            self.graph.add((unit_uri, RDF.type, self.time.TemporalUnit))
            self.graph.add((unit_uri, RDFS.label, Literal(unit, lang="en")))
            self.graph.add((unit_uri, RDFS.comment, Literal(f"Represents a time unit of one {unit}.", lang="en")))
        
        # Create the duration
        self.graph.add((duration_uri, RDF.type, self.time.Duration))
        self.graph.add((duration_uri, RDFS.label, Literal(f"Duration of {amount} {unit}{'s' if amount != 1 else ''}", lang="en")))
        self.graph.add((duration_uri, RDFS.comment, Literal(f"A time duration of {amount} {unit}{'s' if amount != 1 else ''}.", lang="en")))
        self.graph.add((duration_uri, self.time.numericDuration, Literal(amount, datatype=XSD.float)))
        self.graph.add((duration_uri, self.time.unitType, unit_uri))
        
        # Add an xsd:duration literal as well (format: P[n]Y[n]M[n]DT[n]H[n]M[n]S)
        if unit == "day":
            xsd_duration = f"P{int(amount)}D"  # Make sure amount is an integer for days
        elif unit == "week":
            xsd_duration = f"P{int(amount)}W"
        elif unit == "month":
            xsd_duration = f"P{int(amount)}M"
        elif unit == "year":
            xsd_duration = f"P{int(amount)}Y"
        else:
            # Default to days if unit not recognized
            xsd_duration = f"P{int(amount)}D"
            
        self.graph.add((duration_uri, self.time.hasDuration, Literal(xsd_duration, datatype=XSD.duration)))
        
        return duration_uri
    
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
        
        # Create URIs
        track_uri = URIRef(TRACK_IRI_PATTERN.format(track_id))
        chart_entry_uri = URIRef(CHART_ENTRY_IRI_PATTERN.format(chart_entry_id))
        time_instant_uri = self._get_or_create_time_instant(chart_date)
        chart_uri = self.charts['hot_100']
        
        # Create a time interval and duration for the chart week
        interval_uri = self._create_time_interval(chart_date, 7)
        duration_uri = self._get_or_create_duration(7, "day")
        
        # Add track if it doesn't exist
        if track_id not in self.tracks:
            self.tracks[track_id] = track_uri
            self.graph.add((track_uri, RDF.type, self.mo.Track))
            self.graph.add((track_uri, RDFS.label, Literal(song_title, lang="en")))
            self.graph.add((track_uri, RDFS.comment, Literal(f"Track titled '{song_title}' by {artist_name}.", lang="en")))
            
            # Process artist(s)
            self._process_artists(artist_name, track_uri)
            
            # Add lyrics if available (direct from match_csv_to_lyrics or match_csv_to_enriched_lyrics)
            if hasattr(self, 'lyrics_dict') and track_id in self.lyrics_dict:
                lyrics_data = self.lyrics_dict[track_id]
                
                # Handle both simple text lyrics and structured lyrics data
                if isinstance(lyrics_data, dict):
                    # This is from the enriched lyrics CSV
                    # Add the main lyrics
                    if 'lyrics' in lyrics_data and lyrics_data['lyrics']:
                        self.graph.add((track_uri, self.mo.hasLyrics, Literal(lyrics_data['lyrics'])))
                    
                    # Add language information if available
                    if 'language' in lyrics_data and lyrics_data['language']:
                        lang_code = lyrics_data['language'].lower()
                        # Create or reuse language entity
                        if lang_code not in self.languages:
                            lang_uri = URIRef(f"{NAMESPACES['mo']}language_{lang_code}")
                            self.languages[lang_code] = lang_uri
                            self.graph.add((lang_uri, RDF.type, self.mo.Language))
                            self.graph.add((lang_uri, RDFS.label, Literal(lang_code.upper(), lang="en")))
                            self.graph.add((lang_uri, RDFS.comment, Literal(f"Represents the {lang_code.upper()} language.", lang="en")))
                        else:
                            lang_uri = self.languages[lang_code]
                            
                        self.graph.add((track_uri, self.mo.hasLanguage, lang_uri))
                    
                    # Add translated lyrics if available
                    if 'translated' in lyrics_data and lyrics_data['translated'] and not pd.isna(lyrics_data['translated']):
                        self.graph.add((track_uri, self.mo.hasTranslatedLyrics, Literal(lyrics_data['translated'])))
                    
                    # Add theme if available
                    if 'theme' in lyrics_data and lyrics_data['theme'] and not pd.isna(lyrics_data['theme']):
                        self.graph.add((track_uri, self.mo.hasTheme, Literal(lyrics_data['theme'])))
                else:
                    # This is just plain lyrics text from the original approach
                    self.graph.add((track_uri, self.mo.hasLyrics, Literal(lyrics_data)))
        
        # Create chart entry
        self.graph.add((chart_entry_uri, RDF.type, self.ex.ChartEntry))
        self.graph.add((chart_entry_uri, RDFS.label, Literal(f"{song_title} at position {rank} on {chart_date}", lang="en")))
        self.graph.add((chart_entry_uri, RDFS.comment, Literal(f"Chart entry for '{song_title}' at position {rank} on the Billboard Hot 100 chart dated {chart_date}.", lang="en")))
        self.graph.add((chart_entry_uri, self.ex.chartPosition, Literal(rank, datatype=XSD.integer)))
        self.graph.add((chart_entry_uri, self.ex.chart, chart_uri))
        self.graph.add((chart_entry_uri, self.ex.inChart, chart_uri))  # Add both properties from billboard.ttl
        self.graph.add((chart_entry_uri, self.time.inDate, time_instant_uri))
        self.graph.add((chart_entry_uri, self.mo.forTrack, track_uri))
        self.graph.add((chart_entry_uri, self.ex.hasInterval, interval_uri))  # Add the interval
        self.graph.add((chart_entry_uri, self.ex.hasDuration, duration_uri))  # Add the duration
        
        # Update chart run
        self._update_chart_run(track_uri, track_id, chart_entry_uri, time_instant_uri, chart_date)
    
    def _process_artists(self, artist_text, track_uri):
        """
        Process artist field from CSV and create artist entities.
        Handles various collaboration formats and ensures only individual artists are created.
        """
        # First normalize the artist text to handle different collaboration formats
        normalized_text = artist_text
        
        # Handle various forms of artist collaborations
        # Define all patterns to split - using word boundaries and more careful patterns
        collaboration_patterns = [
            " feat. ", " ft. ", " featuring ", 
            " & ", 
            ", ", 
            " with ", 
            r" x ", # Only match "x" when it's surrounded by spaces, not part of names like Alex
            " + ", 
            " vs. ", " versus "
        ]
        # Don't use "and" as it's too common in artist names
        
        # Split by each pattern, keeping the full hierarchy of splits
        artists_to_process = [normalized_text]
        for pattern in collaboration_patterns:
            new_artists_list = []
            for artist in artists_to_process:
                if pattern in artist:  # Simple string check works for all our patterns
                    splits = artist.split(pattern)
                    new_artists_list.extend([a.strip() for a in splits if a.strip()])
                else:
                    new_artists_list.append(artist)
            artists_to_process = new_artists_list
        
        # Remove duplicates while preserving order
        artists = []
        for artist in artists_to_process:
            if artist not in artists:
                artists.append(artist)
        
        for artist_name in artists:
            artist_name = artist_name.strip()  # Clean up the name
            # Skip empty names or obviously incomplete fragments
            if not artist_name or len(artist_name) < 2:
                continue
                
            # Remove any leftover parenthetical phrases that might contain "feat" etc.
            artist_name = re.sub(r'\([^)]*\)', '', artist_name).strip()
            artist_name = re.sub(r'\[[^\]]*\]', '', artist_name).strip()
            
            artist_id = generate_entity_id(artist_name)
            artist_uri = URIRef(ARTIST_IRI_PATTERN.format(artist_id))
            
            if artist_id not in self.artists:
                self.artists[artist_id] = artist_uri
                self.graph.add((artist_uri, RDF.type, self.mo.MusicArtist))
                self.graph.add((artist_uri, RDFS.label, Literal(artist_name, lang="en")))
                self.graph.add((artist_uri, RDFS.comment, Literal(f"Music artist or band named '{artist_name}'.", lang="en")))
                
                # Default to unknown gender for artists from CSV
                gender_uri = self.genders.get("unknown")
                if gender_uri:
                    self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
            
            # Link track to artist
            self.graph.add((track_uri, self.mo.hasMusicArtist, artist_uri))
            # Add inverse relationship - artist to track
            self.graph.add((artist_uri, self.mo.hasTrack, track_uri))
    
    def _extract_record_from_title(self, track_title, track_uri):
        """Try to extract record information from a track title (for albums, EPs, etc.)"""
        # Common patterns indicating albums or EPs
        album_patterns = [
            r'from the album "(.*?)"',
            r'from "(.*?)" album',
            r'\(from "(.*?)"\)'
        ]
        
        for pattern in album_patterns:
            match = re.search(pattern, track_title, re.IGNORECASE)
            if match:
                album_title = match.group(1)
                record_id = generate_entity_id(album_title)
                
                if record_id not in self.records:
                    record_uri = URIRef(RECORD_IRI_PATTERN.format(record_id))
                    self.records[record_id] = record_uri
                    
                    self.graph.add((record_uri, RDF.type, self.mo.Record))
                    self.graph.add((record_uri, RDFS.label, Literal(album_title, lang="en")))
                    
                    # Link track to record
                    self.graph.add((track_uri, self.mo.published_as, record_uri))
                    
                    return record_uri
        
        return None
    
    def _normalize_track_title(self, track_name):
        """
        Apply advanced normalization to track names to improve matching:
        - Remove common variations like "(Radio Edit)", "(Live)", etc.
        - Standardize featuring artist annotations
        - Remove punctuation and lowercase
        """
        if not track_name:
            return ""
            
        # Convert to lowercase
        normalized = track_name.lower()
        
        # Remove common suffixes in parentheses or brackets
        common_suffixes = [
            r'\(radio edit\)',
            r'\(album version\)',
            r'\(original mix\)',
            r'\(original version\)',
            r'\(extended version\)',
            r'\(single version\)',
            r'\(explicit\)',
            r'\(clean\)',
            r'\(live\)',
            r'\(remix\)',
            r'\[radio edit\]',
            r'\[explicit\]',
            r'\[clean\]'
        ]
        
        for suffix in common_suffixes:
            normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
        
        # Standardize featuring artists
        normalized = re.sub(r'feat\.', 'featuring', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'ft\.', 'featuring', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'featuring', '', normalized, flags=re.IGNORECASE)  # Remove featuring entirely
        
        # Remove common words that don't add meaningful distinction
        filler_words = [r'\bthe\b', r'\band\b', r'\bwith\b']
        for word in filler_words:
            normalized = re.sub(word, '', normalized, flags=re.IGNORECASE)
        
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _artists_match(self, json_artists, csv_artist_id):
        """
        Check if any artist from the JSON data matches the CSV artist.
        Uses more relaxed matching to handle spelling variations and name format differences.
        """
        if not json_artists or not csv_artist_id:
            return False
            
        # Try to extract artist names from the CSV artist ID
        csv_artists = csv_artist_id.split('_')
        
        # Try to get the original artist name from RDFS:label if available
        csv_artist_uri = None
        for _, artist_uri in self.artists.items():
            if str(artist_uri).endswith(csv_artist_id):
                csv_artist_uri = artist_uri
                break
                
        csv_artist_names = []
        if csv_artist_uri:
            for _, _, label in self.graph.triples((csv_artist_uri, RDFS.label, None)):
                csv_artist_names.append(str(label))
        
        # If we couldn't find labels, fall back to ID-based names
        if not csv_artist_names:
            # It might be a single artist name with underscores
            csv_artist_name = csv_artist_id.replace('_', ' ')
            csv_artist_names = [csv_artist_name]
        
        # Normalize all artist names
        normalized_json_artists = [clean_entity_name(a.lower()) for a in json_artists]
        normalized_csv_artists = [clean_entity_name(a.lower()) for a in csv_artist_names]
        
        # Check for direct matches first
        for json_artist in normalized_json_artists:
            for csv_artist in normalized_csv_artists:
                # Direct match
                if json_artist == csv_artist:
                    return True
                
                # Check if one is a substring of the other (for example "Jay-Z" vs "Jay Z")
                if json_artist in csv_artist or csv_artist in json_artist:
                    return True
                
                # Fuzzy match with a lower threshold (60+) to capture more matches
                similarity = fuzz.ratio(json_artist, csv_artist)
                if similarity >= 60:
                    return True
                
                # Try token_sort_ratio for word reordering
                token_similarity = fuzz.token_sort_ratio(json_artist, csv_artist)
                if token_similarity >= 70:
                    return True
        
        # Relaxed match: If we've made it this far, try one more check with a very low threshold
        # This is more permissive and may introduce some false positives, but will maximize matches
        for json_artist in normalized_json_artists:
            for csv_artist in normalized_csv_artists:
                if len(json_artist) > 2 and len(csv_artist) > 2:  # Only for non-trivial artist names
                    # Final attempt with a lower threshold for artists with shared tokens
                    if any(token in csv_artist for token in json_artist.split('_') if len(token) > 3):
                        return True
        
        return False

    def _validate_xsd_date(self, date_str):
        """
        Validate and normalize a date string to XSD date format (YYYY-MM-DD).
        If the date string is not in a valid format, returns None.
        """
        if not date_str:
            return None
            
        # Check for full YYYY-MM-DD format
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            try:
                # Verify it's a valid date
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                return None
                
        # Check for YYYY-MM format (add day)
        if re.match(r"^\d{4}-\d{2}$", date_str):
            try:
                year, month = date_str.split('-')
                # Add day as "01"
                return f"{year}-{month}-01"
            except ValueError:
                return None
        
        # Check for just year (YYYY)
        if re.match(r"^\d{4}$", date_str):
            # Add January 1st
            return f"{date_str}-01-01"
            
        return None

    def map_json_data(self, json_data):
        """Map track information from JSON to RDF triples"""
        
        # Track statistics for reporting
        matched_tracks = 0
        skipped_tracks = 0
        
        # Preprocess all artist data from JSON first to capture metadata
        # This ensures we get artist info even if their tracks don't match
        person_uri_map = self.preprocess_json_artists(json_data)
        
        # Create a normalized title index of existing tracks from CSV
        # This is the key improvement - focus on normalized title matching
        normalized_track_index = {}
        
        # Function for basic title normalization (same as in our analysis)
        def normalize_title(title):
            if not title:
                return ""
            # Convert to lowercase
            title = title.lower()
            # Remove featuring artists
            title = re.sub(r'\s+(?:feat|ft|featuring)\.?\s+.*', '', title, flags=re.IGNORECASE)
            # Remove text in parentheses
            title = re.sub(r'\([^)]*\)', '', title)
            # Remove text in brackets
            title = re.sub(r'\[[^\]]*\]', '', title)
            # Standardize slashes (for medleys)
            title = re.sub(r'\s*/\s*', '/', title)
            # Remove special characters (except slash for medleys)
            title = re.sub(r'[^\w\s/]', '', title)
            # Remove common filler words
            for word in [r'\bthe\b', r'\band\b', r'\bwith\b', r'\ba\b', r'\ban\b', r'\bof\b']:
                title = re.sub(word, '', title, flags=re.IGNORECASE)
            # Normalize whitespace
            title = re.sub(r'\s+', ' ', title).strip()
            return title
        
        # Build the normalized title index from existing tracks
        for track_id, track_uri in self.tracks.items():
            # The track ID format is: clean_title_clean_artist_hash
            # Extract the parts before the hash (last segment)
            parts = track_id.split('_')
            if len(parts) > 1:
                # In analyze_title_matches.py, we're looking at the raw song title from CSV
                # so here we should fetch the original track title from the graph
                track_title = None
                for _, _, label in self.graph.triples((track_uri, RDFS.label, None)):
                    track_title = str(label)
                    break
                
                # If we can't find a label, fall back to extracting from ID
                if not track_title:
                    # Last part is the hash (6 chars)
                    # Remove the hash and the artist from the ID
                    track_parts = parts[:-1]  # Remove hash
                    # Just use the whole reconstructed string as a fallback
                    track_title = '_'.join(track_parts).replace('_', ' ')
                
                # Normalize the track title
                norm_title = normalize_title(track_title)
                
                # Store with artist info for better matching
                if norm_title not in normalized_track_index:
                    normalized_track_index[norm_title] = []
                normalized_track_index[norm_title].append((track_id, track_uri))
        
        print(f"Built normalized index of {len(normalized_track_index)} unique track titles")
        
        # Process each JSON track
        for key, data in json_data.items():
            track_name = data.get('track', '')
            if not track_name:
                skipped_tracks += 1
                continue
                
            # Extract artists for additional matching criteria if needed
            artists = []
            if 'artist' in data and data['artist']:
                for artist_data in data['artist']:
                    artist_name = artist_data.get('artist_name', '')
                    if artist_name:
                        artists.append(artist_name)
            
            primary_artist = artists[0] if artists else "unknown_artist"
            
            # Normalize the JSON track title
            normalized_json_title = normalize_title(track_name)
            
            # Look for exact match in normalized titles
            track_uri = None
            track_exists = False
            
            if normalized_json_title in normalized_track_index:
                # We have a normalized title match, but we still need to verify the artist
                candidates = normalized_track_index[normalized_json_title]
                
                # Try to find the best artist match among candidates
                for candidate_id, candidate_uri in candidates:
                    # Extract original track ID for artist matching
                    # Check if any of our artists match the candidate
                    if any(self._artists_match([artist], candidate_id) for artist in artists):
                        track_uri = candidate_uri
                        track_exists = True
                        break
                
                # If we couldn't match by artist, just use the first candidate
                # This is reasonable since we have the same normalized title
                if not track_exists and candidates:
                    track_uri = candidates[0][1]
                    track_exists = True
            
            # If we still don't have a match, try token-based fuzzy matching
            if not track_exists:
                best_match = None
                best_score = 0
                best_uri = None
                
                # Try fuzzy matching for all titles
                for norm_title, candidates in normalized_track_index.items():
                    # Try several fuzzy matching approaches
                    
                    # 1. Basic ratio (overall string similarity)
                    ratio_score = fuzz.ratio(normalized_json_title, norm_title)
                    
                    # 2. Token sort ratio (handles word reordering)
                    token_sort_score = fuzz.token_sort_ratio(normalized_json_title, norm_title)
                    
                    # 3. Token set ratio (handles partial matches and subsets)
                    token_set_score = fuzz.token_set_ratio(normalized_json_title, norm_title)
                    
                    # Take the best score from the three approaches
                    score = max(ratio_score, token_sort_score, token_set_score)
                    
                    # Lower threshold (60) to catch more matches
                    if score > 60 and score > best_score:
                        # Try to match by artist for better accuracy
                        for candidate_id, candidate_uri in candidates:
                            if any(self._artists_match([artist], candidate_id) for artist in artists):
                                best_match = candidate_id
                                best_score = score
                                best_uri = candidate_uri
                                break
                        
                        # If no artist match but better score, still consider it
                        if not best_match and score > best_score:
                            best_match = candidates[0][0]
                            best_score = score
                            best_uri = candidates[0][1]
                
                if best_uri:
                    track_uri = best_uri
                    track_exists = True
            
            # If we still don't have a match, skip this JSON track
            if not track_exists:
                skipped_tracks += 1
                continue  # Skip to the next JSON track
            
            # Track was found, count it and proceed with enrichment
            matched_tracks += 1
            
            # The rest of the method continues as before - enriching the track with additional data
            # Add additional track properties if available
            if 'year' in data and data['year']:
                try:
                    year = int(data['year'])
                    self.graph.add((track_uri, self.mo.year, Literal(year, datatype=XSD.integer)))
                except (ValueError, TypeError):
                    pass
                    
            if 'duration' in data and data['duration']:
                try:
                    duration_seconds = float(data['duration'])
                    self.graph.add((track_uri, self.mo.duration, Literal(duration_seconds, datatype=XSD.decimal)))
                except (ValueError, TypeError):
                    pass
            
            # Helper function to get or create a person entity
            def get_or_create_person_entity(person_name):
                # First check if this person already exists in our map
                if person_name in person_uri_map:
                    return person_uri_map[person_name]
                
                # If not in our map, check if this person exists as an artist
                person_id = generate_entity_id(person_name)
                artist_uri = URIRef(ARTIST_IRI_PATTERN.format(person_id))
                
                # Try entity resolution for artist
                artist_found, matching_uri, matched_id = find_matching_artist(
                    person_name, person_id, self.artists
                )
                
                if artist_found:
                    # Use the existing artist URI
                    person_uri = matching_uri
                    # Update our artists map with this alternate ID to help future lookups
                    if person_id != matched_id:
                        self.artists[person_id] = matching_uri
                else:
                    # Next check if this person exists as a writer
                    if person_id in self.writers:
                        person_uri = self.writers[person_id]
                    # Or as a producer
                    elif person_id in self.producers:
                        person_uri = self.producers[person_id]
                    # Or as any other role
                    elif person_id in self.arrangers:
                        person_uri = self.arrangers[person_id]
                    elif person_id in self.engineers:
                        person_uri = self.engineers[person_id]
                    elif person_id in self.mixers:
                        person_uri = self.mixers[person_id]
                    elif person_id in self.vocalists:
                        person_uri = self.vocalists[person_id]
                    elif person_id in self.instrumentalists:
                        person_uri = self.instrumentalists[person_id]
                    elif person_id in self.recorders:
                        person_uri = self.recorders[person_id]
                    else:
                        # Create a new person entity if not found in any role
                        person_uri = artist_uri  # Use the artist URI pattern for all persons
                        self.graph.add((person_uri, RDFS.label, Literal(person_name, lang="en")))
                        
                        # Default to unknown gender if not specified
                        gender_uri = self.genders.get("unknown")
                        if gender_uri:
                            self.graph.add((person_uri, self.mo.hasGender, gender_uri))
                
                # Store in our map for future reference
                person_uri_map[person_name] = person_uri
                return person_uri
            
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
            
            # Process record label
            if 'label' in data and data['label']:
                label_names = data['label']
                # Handle both single label string and list of labels
                if not isinstance(label_names, list):
                    label_names = [label_names]  # Convert to list for uniform processing
                
                for label_name in label_names:
                    if not label_name:  # Skip empty values
                        continue
                        
                    # Ensure label_name is a string
                    if not isinstance(label_name, str):
                        continue
                        
                    label_id = generate_entity_id(label_name)
                    label_uri = URIRef(LABEL_IRI_PATTERN.format(label_id))
                    
                    if label_id not in self.labels:
                        self.labels[label_id] = label_uri
                        self.graph.add((label_uri, RDF.type, self.mo.Label))
                        self.graph.add((label_uri, RDFS.label, Literal(label_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasLabel, label_uri))
                    # Add inverse relationship
                    self.graph.add((label_uri, self.mo.labelForTrack, track_uri))
            
            # Process artists
            if 'artist' in data and data['artist']:
                artists_to_add = []
                # First collect all artist names, handling collaborations properly
                all_artists_to_process = {}  # Initialize the dictionary here
                for artist_data in data['artist']:
                    artist_name = artist_data.get('artist_name', '')
                    if not artist_name:
                        continue
                    
                    # Process each artist string for potential collaborations
                    collaboration_patterns = [
                        " feat. ", " ft. ", " featuring ", 
                        " & ", 
                        ", ", 
                        " with ", 
                        r" x ", # Only match "x" when it's surrounded by spaces, not part of names like Alex
                        " + ", 
                        " vs. ", " versus "
                    ]
                    # Don't use "and" as it's too common in artist names
                    
                    # Split by each pattern, recursively
                    artists_from_name = [artist_name]
                    for pattern in collaboration_patterns:
                        new_list = []
                        for artist in artists_from_name:
                            if pattern in artist:  # Simple string check works for all our patterns
                                splits = artist.split(pattern)
                                new_list.extend([a.strip() for a in splits if a.strip()])
                            else:
                                new_list.append(artist)
                        artists_from_name = new_list
                    
                    # Clean up and add to the artists list
                    for individual_artist in artists_from_name:
                        # Skip empty names or obviously incomplete fragments
                        if not individual_artist or len(individual_artist) < 2:
                            continue
                            
                        # Remove any parenthetical phrases that might contain "feat" etc.
                        individual_artist = re.sub(r'\([^)]*\)', '', individual_artist).strip()
                        individual_artist = re.sub(r'\[[^\]]*\]', '', individual_artist).strip()
                        
                        if individual_artist and individual_artist not in all_artists_to_process:
                            all_artists_to_process[individual_artist] = artist_data if isinstance(artist_data, dict) else {}
                
                # Now process each individual artist
                for artist_name in all_artists_to_process:
                    # Skip if we've already processed this artist
                    if artist_name in person_uri_map:
                        continue
                    
                    artist_count += 1
                    
                    # Create a normalized artist index for better matching if not already created
                    if 'normalized_artist_index' not in locals():
                        normalized_artist_index = self._create_normalized_artist_index()
                    
                    # Normalize the artist name for matching
                    normalized_json_artist = self._normalize_artist_name(artist_name)
                    
                    # Check for a matching artist in our normalized index
                    artist_uri = None
                    artist_id = None
                    artist_exists = False
                    
                    if normalized_json_artist in normalized_artist_index:
                        # We have a normalized name match
                        candidates = normalized_artist_index[normalized_json_artist]
                        
                        # Just use the first match for simplicity
                        if candidates:
                            artist_id, artist_uri, _ = candidates[0]
                            artist_exists = True
                            matched_artists += 1
                    
                    # If no match found, try fuzzy matching
                    if not artist_exists:
                        best_match = None
                        best_score = 0
                        
                        for norm_name, candidates in normalized_artist_index.items():
                            # Skip very short names to avoid false positives
                            if len(norm_name) < 3 or len(normalized_json_artist) < 3:
                                continue
                                
                            # Use token sort ratio for better handling of word order differences
                            score = fuzz.token_sort_ratio(normalized_json_artist, norm_name)
                            
                            # Only consider high-confidence matches
                            if score > 85 and score > best_score:
                                best_score = score
                                best_match = candidates[0]  # Take the first candidate
                        
                        if best_match:
                            artist_id, artist_uri, _ = best_match
                            artist_exists = True
                            matched_artists += 1
                    
                    # If still no match, create a new artist
                    if not artist_exists:
                        artist_id = generate_entity_id(artist_name)
                        artist_uri = URIRef(ARTIST_IRI_PATTERN.format(artist_id))
                        new_artists += 1
                        
                        # Create new artist entity
                        self.graph.add((artist_uri, RDF.type, self.mo.MusicArtist))
                        self.graph.add((artist_uri, RDFS.label, Literal(artist_name, lang="en")))
                        self.graph.add((artist_uri, RDFS.comment, Literal(f"Music artist or band named '{artist_name}'.", lang="en")))
                        
                        # Default to unknown gender
                        gender_uri = self.genders.get("unknown")
                        if gender_uri:
                            self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
                    
                    # Store in our dictionaries
                    person_uri_map[artist_name] = artist_uri
                    self.artists[artist_id] = artist_uri
                    
                    # Add additional artist information if available
                    if isinstance(all_artists_to_process[artist_name], dict):
                        if 'legal_name' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['legal_name']:
                            legal_names = all_artists_to_process[artist_name]['legal_name']
                            if isinstance(legal_names, list):
                                for legal_name in legal_names:
                                    if legal_name:
                                        self.graph.add((artist_uri, self.mo.legalName, Literal(legal_name, lang="en")))
                            else:
                                self.graph.add((artist_uri, self.mo.legalName, Literal(legal_names, lang="en")))
                                
                        if 'gender' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['gender']:
                            gender_str = all_artists_to_process[artist_name]['gender'].lower()
                            if gender_str in self.genders:
                                self.graph.add((artist_uri, self.mo.hasGender, self.genders[gender_str]))
                                
                        if 'date_of_birth' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['date_of_birth']:
                            birth_date = all_artists_to_process[artist_name]['date_of_birth']
                            artists_with_dob += 1
                            
                            # Handle incomplete dates (YYYY or YYYY-MM) by appending default month/day values
                            if re.match(r'^\d{4}$', birth_date):  # Just a year
                                birth_date = f"{birth_date}-01-01"  # Use January 1st
                            elif re.match(r'^\d{4}-\d{2}$', birth_date):  # Year and month
                                birth_date = f"{birth_date}-01"  # Use the 1st day of month
                            
                            try:
                                # Only add as XSD.date if it's a valid date format
                                if re.match(r'^\d{4}-\d{2}-\d{2}$', birth_date):
                                    self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(birth_date, datatype=XSD.date)))
                                else:
                                    # Fall back to string literal if not a valid date format
                                    self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(birth_date)))
                            except Exception as e:
                                # If there's any error, fall back to string
                                print(f"Warning: Invalid birth date '{birth_date}', storing as string")
                                self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(birth_date)))
                                
                        if 'country' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['country']:
                            country = all_artists_to_process[artist_name]['country']
                            self.graph.add((artist_uri, self.mo.country, Literal(country, lang="en")))
                            
                        if 'area' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['area']:
                            area = all_artists_to_process[artist_name]['area']
                            if area:  # Check if area is not None
                                self.graph.add((artist_uri, self.mo.area, Literal(area, lang="en")))
            
            # Process writers
            if 'writer' in data and data['writer']:
                for writer_name in data['writer']:
                    if not writer_name:
                        continue
                    
                    # Get or create person entity
                    writer_uri = get_or_create_person_entity(writer_name)
                    
                    # Add writer type if not already present
                    self.graph.add((writer_uri, RDF.type, self.mo.MusicWriter))
                    
                    # Add writer to the writers dictionary if not already there
                    writer_id = generate_entity_id(writer_name)
                    self.writers[writer_id] = writer_uri
                    
                    # Link track to writer
                    self.graph.add((track_uri, self.mo.hasWriter, writer_uri))
                    # Add inverse relationship
                    self.graph.add((writer_uri, self.mo.wroteTrack, track_uri))
            
            # Process composers (as producers)
            if 'composer' in data and data['composer']:
                for composer_name in data['composer']:
                    if not composer_name:
                        continue
                    
                    # Get or create person entity
                    composer_uri = get_or_create_person_entity(composer_name)
                    
                    # Add producer type if not already present
                    self.graph.add((composer_uri, RDF.type, self.mo.MusicProducer))
                    
                    # Add producer to the producers dictionary if not already there
                    composer_id = generate_entity_id(composer_name)
                    self.producers[composer_id] = composer_uri
                    
                    # Link track to producer
                    self.graph.add((track_uri, self.mo.hasProducer, composer_uri))
                    # Add inverse relationship
                    self.graph.add((composer_uri, self.mo.producedTrack, track_uri))
            
            # Process tags as genres
            if 'tags' in data and data['tags']:
                for tag in data['tags']:
                    if not tag:
                        continue
                    
                    # Convert tag to genre
                    genre_id = generate_entity_id(tag)
                    
                    if genre_id not in self.genres:
                        genre_uri = URIRef(GENRE_IRI_PATTERN.format(genre_id))
                        self.genres[genre_id] = genre_uri
                        self.graph.add((genre_uri, RDF.type, self.mo.Genre))
                        self.graph.add((genre_uri, RDFS.label, Literal(tag, lang="en")))
                        
                        self.graph.add((track_uri, self.mo.hasGenre, genre_uri))
                    else:
                        genre_uri = self.genres[genre_id]
                        self.graph.add((track_uri, self.mo.hasGenre, genre_uri))
            
            # Process arranger properly as Arranger
            if 'arranger' in data and data['arranger']:
                for arranger_name in data['arranger']:
                    if not arranger_name:
                        continue
                    
                    # Get or create person entity
                    arranger_uri = get_or_create_person_entity(arranger_name)
                    
                    # Add arranger type if not already present
                    self.graph.add((arranger_uri, RDF.type, self.mo.Arranger))
                    
                    # Add arranger to the arrangers dictionary if not already there
                    arranger_id = generate_entity_id(arranger_name)
                    self.arrangers[arranger_id] = arranger_uri
                    
                    # Link track to arranger
                    self.graph.add((track_uri, self.mo.hasArranger, arranger_uri))
                    # Add inverse relationship
                    self.graph.add((arranger_uri, self.mo.arrangedTrack, track_uri))
            
            # Process engineer
            if 'engineer' in data and data['engineer']:
                for engineer_name in data['engineer']:
                    if not engineer_name:
                        continue
                    
                    # Get or create person entity
                    engineer_uri = get_or_create_person_entity(engineer_name)
                    
                    # Add engineer type if not already present
                    self.graph.add((engineer_uri, RDF.type, self.mo.Engineer))
                    
                    # Add engineer to the engineers dictionary if not already there
                    engineer_id = generate_entity_id(engineer_name)
                    self.engineers[engineer_id] = engineer_uri
                    
                    # Link track to engineer
                    self.graph.add((track_uri, self.mo.hasEngineer, engineer_uri))
                    # Add inverse relationship
                    self.graph.add((engineer_uri, self.mo.engineeredTrack, track_uri))
            
            # Process mix
            if 'mix' in data and data['mix']:
                for mixer_name in data['mix']:
                    if not mixer_name:
                        continue
                    
                    # Get or create person entity
                    mixer_uri = get_or_create_person_entity(mixer_name)
                    
                    # Add mixer type if not already present
                    self.graph.add((mixer_uri, RDF.type, self.mo.Mixer))
                    
                    # Add mixer to the mixers dictionary if not already there
                    mixer_id = generate_entity_id(mixer_name)
                    self.mixers[mixer_id] = mixer_uri
                    
                    # Link track to mixer
                    self.graph.add((track_uri, self.mo.hasMixer, mixer_uri))
                    # Add inverse relationship
                    self.graph.add((mixer_uri, self.mo.mixedTrack, track_uri))
            
            # Process vocalist
            if 'vocal' in data and data['vocal']:
                for vocalist_name in data['vocal']:
                    if not vocalist_name:
                        continue
                    
                    # Get or create person entity
                    vocalist_uri = get_or_create_person_entity(vocalist_name)
                    
                    # Add vocalist type if not already present
                    self.graph.add((vocalist_uri, RDF.type, self.mo.Vocalist))
                    
                    # Add vocalist to the vocalists dictionary if not already there
                    vocalist_id = generate_entity_id(vocalist_name)
                    self.vocalists[vocalist_id] = vocalist_uri
                    
                    # Link track to vocalist
                    self.graph.add((track_uri, self.mo.hasVocalist, vocalist_uri))
                    # Add inverse relationship
                    self.graph.add((vocalist_uri, self.mo.sangTrack, track_uri))
            
            # Process instrumentalist
            if 'instrument' in data and data['instrument']:
                for instrumentalist_name in data['instrument']:
                    if not instrumentalist_name:
                        continue
                    
                    # Get or create person entity
                    instrumentalist_uri = get_or_create_person_entity(instrumentalist_name)
                    
                    # Add instrumentalist type if not already present
                    self.graph.add((instrumentalist_uri, RDF.type, self.mo.Instrumentalist))
                    
                    # Add instrumentalist to the instrumentalists dictionary if not already there
                    instrumentalist_id = generate_entity_id(instrumentalist_name)
                    self.instrumentalists[instrumentalist_id] = instrumentalist_uri
                    
                    # Link track to instrumentalist
                    self.graph.add((track_uri, self.mo.hasInstrumentalist, instrumentalist_uri))
            
            # Process recorder
            if 'recording' in data and data['recording']:
                for recorder_name in data['recording']:
                    if not recorder_name:
                        continue
                    
                    # Get or create person entity
                    recorder_uri = get_or_create_person_entity(recorder_name)
                    
                    # Add recorder type if not already present
                    self.graph.add((recorder_uri, RDF.type, self.mo.Recorder))
                    
                    # Add recorder to the recorders dictionary if not already there
                    recorder_id = generate_entity_id(recorder_name)
                    self.recorders[recorder_id] = recorder_uri
                    
                    # Link track to recorder
                    self.graph.add((track_uri, self.mo.hasRecorder, recorder_uri))
                    # Add inverse relationship
                    self.graph.add((recorder_uri, self.mo.recordedTrack, track_uri))
            
            # Process producer if not handled by composer mapping
            if 'producer' in data and data['producer']:
                for producer_name in data['producer']:
                    if not producer_name:
                        continue
                    
                    # Get or create person entity
                    producer_uri = get_or_create_person_entity(producer_name)
                    
                    # Add producer type if not already present
                    self.graph.add((producer_uri, RDF.type, self.mo.MusicProducer))
                    
                    # Add producer to the producers dictionary if not already there
                    producer_id = generate_entity_id(producer_name)
                    self.producers[producer_id] = producer_uri
                    
                    # Link track to producer
                    self.graph.add((track_uri, self.mo.hasProducer, producer_uri))
                    # Add inverse relationship
                    self.graph.add((producer_uri, self.mo.producedTrack, track_uri))
        
        print(f"Processed JSON data: {matched_tracks} tracks matched to existing tracks, {skipped_tracks} tracks skipped (no match found)")
        
        return self.tracks
    
    def _update_chart_run(self, track_uri, track_id, chart_entry_uri, time_instant_uri, chart_date):
        """
        Update chart run information for a track.
        This method tracks how long a song has been in the charts by creating or updating chart run entities.
        It also establishes temporal relationships between chart entries using time:before and time:after.
        
        A chart run is defined as consecutive weeks on the chart. If a song leaves the chart
        and re-enters later, a new chart run is created.
        
        Args:
            track_uri (URIRef): URI of the track
            track_id (str): ID of the track
            chart_entry_uri (URIRef): URI of the current chart entry
            time_instant_uri (URIRef): URI of the time instant for this chart entry
            chart_date (str): Date string of the current chart entry
        """
        # Initialize track's chart entries collection if it doesn't exist
        if track_id not in self.track_chart_entries:
            self.track_chart_entries[track_id] = {}
        
        # Store this chart entry for later reference
        self.track_chart_entries[track_id][chart_date] = {
            'entry_uri': chart_entry_uri,
            'instant_uri': time_instant_uri,
            'date': chart_date
        }
        
        # Sort all chart entries for this track by date
        sorted_entries = sorted(
            self.track_chart_entries[track_id].values(),
            key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d")  # Ensure proper date sorting
        )
        
        # Add time:before and time:after relationships between consecutive chart entries
        for i in range(len(sorted_entries) - 1):
            earlier_entry = sorted_entries[i]
            later_entry = sorted_entries[i + 1]
            
            # Add time:before relationship (earlier_instant before later_instant)
            self.graph.add((earlier_entry['instant_uri'], self.time.before, later_entry['instant_uri']))
            
            # Add time:after relationship (later_instant after earlier_instant)
            self.graph.add((later_entry['instant_uri'], self.time.after, earlier_entry['instant_uri']))

        # Clear existing chart runs for this track
        # This is a complete rebuild approach whenever a new entry is added
        if hasattr(self, 'track_chart_runs') and track_id in self.track_chart_runs:
            for run in self.track_chart_runs[track_id]:
                # Remove the chart run entity from the graph
                chart_run_uri = run['uri']
                for s, p, o in self.graph.triples((chart_run_uri, None, None)):
                    self.graph.remove((s, p, o))
                # Also remove the back-reference from track to chart run
                self.graph.remove((track_uri, self.ex.hasChartRun, chart_run_uri))
        
        # Initialize chart runs list
        if not hasattr(self, 'track_chart_runs'):
            self.track_chart_runs = {}
        self.track_chart_runs[track_id] = []
        
        # Process entries into runs of consecutive weeks
        # A week is considered consecutive if it's 6-8 days after the previous entry
        # This allows for slight variations in weekly chart publication
        MAX_GAP_DAYS = 8
        MIN_GAP_DAYS = 6
        
        current_run = []
        for i in range(len(sorted_entries)):
            entry = sorted_entries[i]
            entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            
            if not current_run:
                # Start a new run
                current_run = [entry]
                continue
            
            # Get the last entry in the current run
            last_entry = current_run[-1]
            last_date = datetime.strptime(last_entry['date'], "%Y-%m-%d")
            
            # Calculate days between entries
            days_gap = (entry_date - last_date).days
            
            # Check if this entry is consecutive with the last one
            if MIN_GAP_DAYS <= days_gap <= MAX_GAP_DAYS:
                # This is a consecutive week, add to current run
                current_run.append(entry)
            else:
                # This is not consecutive, finish the current run and start a new one
                if current_run:
                    self._create_chart_run_from_entries(track_uri, track_id, current_run)
                current_run = [entry]
        
        # Don't forget the last run
        if current_run:
            self._create_chart_run_from_entries(track_uri, track_id, current_run)
    
    def _create_chart_run_from_entries(self, track_uri, track_id, entries):
        """
        Create a chart run entity from a list of consecutive chart entries
        
        Args:
            track_uri (URIRef): URI of the track
            track_id (str): ID of the track
            entries (list): List of chart entry dictionaries
        """
        if not entries:
            return
            
        # Sort entries by date again to be safe
        sorted_entries = sorted(entries, key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"))
        
        # Get first and last dates
        first_entry = sorted_entries[0]
        last_entry = sorted_entries[-1]
        first_date = first_entry['date']
        last_date = last_entry['date']
        
        # Calculate run duration (include the full week of the last entry)
        start_date = datetime.strptime(first_date, "%Y-%m-%d")
        end_date = datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=6)  # Include full week
        days_duration = (end_date - start_date).days + 1  # +1 to include both start and end days
        
        # Calculate weeks duration (rounded to 1 decimal place)
        weeks_duration = round(days_duration / 7, 1)
        
        # Create run ID and URI
        run_id = f"run_{track_id}_{first_date}"
        chart_run_uri = URIRef(CHART_RUN_IRI_PATTERN.format(run_id))
        
        # Create entry URI list
        entry_uris = [entry['entry_uri'] for entry in sorted_entries]
        
        # Store run information
        run_info = {
            'uri': chart_run_uri,
            'first_date': first_date,
            'last_date': last_date,
            'entries': entry_uris,
            'duration_days': days_duration,
            'duration_weeks': weeks_duration
        }
        
        # Add to the track's chart runs
        self.track_chart_runs[track_id].append(run_info)
        
        # Create the chart run entity in the graph
        self._create_chart_run_entity(chart_run_uri, track_uri, weeks_duration, first_date, unit="week")

    def _create_chart_run_entity(self, chart_run_uri, track_uri, duration, start_date=None, unit="day"):
        """
        Create a new chart run entity in the graph
        
        Args:
            chart_run_uri (URIRef): URI of the chart run
            track_uri (URIRef): URI of the track
            duration (float): Duration value
            start_date (str, optional): The start date of the chart run
            unit (str, optional): The time unit for the duration ("day" or "week")
        """
        # Get track name for better labeling
        track_name = "Unknown Track"
        for _, _, label in self.graph.triples((track_uri, RDFS.label, None)):
            track_name = str(label)
            break
            
        # If start_date wasn't provided, try to extract it from the URI
        if not start_date:
            # Extract the start date from the URI
            uri_str = str(chart_run_uri)
            start_date = "unknown"
            # The URI format should be: http://example.org/billboard#chartRun_run_track_id_YYYY-MM-DD
            parts = uri_str.split('_')
            if len(parts) >= 4:  # Make sure we have enough parts
                # The date should be the last part (or last 3 parts joined with '_')
                possible_date = parts[-3] + '-' + parts[-2] + '-' + parts[-1]
                if re.match(r'^\d{4}-\d{2}-\d{2}$', possible_date):
                    start_date = possible_date
        
        # Create label with weeks information
        duration_label = f"{duration} {unit}{'s' if duration != 1 else ''}"
        
        # Create the chart run entity
        self.graph.add((chart_run_uri, RDF.type, self.ex.ChartRun))
        self.graph.add((chart_run_uri, RDFS.label, Literal(f"Chart run for '{track_name}' starting {start_date} ({duration_label})", lang="en")))
        self.graph.add((chart_run_uri, RDFS.comment, Literal(f"Represents a continuous period of {duration_label} during which the track '{track_name}' appeared on the Billboard Hot 100 chart, starting on {start_date}.", lang="en")))
        self.graph.add((chart_run_uri, self.mo.forTrack, track_uri))
        
        # Create duration
        duration_uri = self._get_or_create_duration(duration, unit)
        self.graph.add((chart_run_uri, self.ex.chartRunDuration, duration_uri))
        
        # Link back to track
        self.graph.add((track_uri, self.ex.hasChartRun, chart_run_uri))
    
    def save_graph(self, output_path):
        """Save the graph to a Turtle file"""
        self.graph.serialize(destination=output_path, format='turtle')
        print(f"Knowledge graph saved to {output_path} with {len(self.graph)} triples")

    def _normalize_artist_name(self, artist_name):
        """
        Apply advanced normalization to artist names to improve matching:
        - Remove prefixes like "The", "DJ", etc.
        - Standardize special characters
        - Remove punctuation and lowercase
        """
        if not artist_name:
            return ""
            
        # Convert to lowercase
        normalized = artist_name.lower()
        
        # Remove common prefixes
        common_prefixes = [r'^the ', r'^dj ', r'^mc']
        for prefix in common_prefixes:
            normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
        
        # Handle special cases
        normalized = re.sub(r'\$', 's', normalized)  # Replace $ with s (e.g., "A$AP" -> "asap")
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove all non-alphanumeric characters
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
        
    def _create_normalized_artist_index(self):
        """Create a normalized index of artists from the graph for better artist matching"""
        print("Creating normalized artist index...")
        
        # Create a normalized artist index
        normalized_artist_index = {}
        
        # Collect all artist URIs
        for artist_id, artist_uri in self.artists.items():
            # Get the artist name from label
            artist_name = None
            for _, _, label in self.graph.triples((artist_uri, RDFS.label, None)):
                artist_name = str(label)
                break
                
            if not artist_name:
                continue
                
            # Normalize the artist name
            norm_name = self._normalize_artist_name(artist_name)
            
            # Store with artist info
            if norm_name not in normalized_artist_index:
                normalized_artist_index[norm_name] = []
            normalized_artist_index[norm_name].append((artist_id, artist_uri, artist_name))
        
        print(f"Built normalized index of {len(normalized_artist_index)} unique artist names")
        return normalized_artist_index
        
    def preprocess_json_artists(self, json_data):
        """
        Extract and process all artist data from JSON, regardless of track matching.
        This ensures we capture artist metadata like date_of_birth, even if their tracks don't match.
        Uses normalized artist names for better matching between CSV and JSON artist data.
        Handles collaborative artist names properly.
        
        Args:
            json_data (dict): JSON data with artist information
        """
        print("Preprocessing artist data from JSON...")
        
        # Create a normalized artist index for better matching
        normalized_artist_index = self._create_normalized_artist_index()
        
        # Track statistics
        artist_count = 0
        artists_with_dob = 0
        matched_artists = 0
        new_artists = 0
        
        # Create a dictionary to map person names to their URIs across all roles
        person_uri_map = {}
        
        # First, collect all unique artist names from JSON data, handling collaborations
        all_artists_to_process = {}  # Use a dict to track artist data
        
        # Process each JSON track for artist data
        for key, data in json_data.items():
            if 'artist' not in data or not data['artist']:
                continue
            
            for artist_data in data['artist']:
                artist_name = artist_data.get('artist_name', '')
                if not artist_name:
                    continue
                
                # Process each artist string for potential collaborations
                collaboration_patterns = [
                    " feat. ", " ft. ", " featuring ", 
                    " & ", 
                    ", ", 
                    " with ", 
                    r" x ", # Only match "x" when it's surrounded by spaces, not part of names like Alex
                    " + ", 
                    " vs. ", " versus "
                ]
                # Don't use "and" as it's too common in artist names
                
                # Split by each pattern, recursively
                artists_from_name = [artist_name]
                for pattern in collaboration_patterns:
                    new_list = []
                    for artist in artists_from_name:
                        if pattern in artist:  # Simple string check works for all our patterns
                            splits = artist.split(pattern)
                            new_list.extend([a.strip() for a in splits if a.strip()])
                        else:
                            new_list.append(artist)
                    artists_from_name = new_list
                
                # Clean up and add to the artists dictionary
                for individual_artist in artists_from_name:
                    # Skip empty names or obviously incomplete fragments
                    if not individual_artist or len(individual_artist) < 2:
                        continue
                    
                    # Remove any parenthetical phrases that might contain "feat" etc.
                    individual_artist = re.sub(r'\([^)]*\)', '', individual_artist).strip()
                    individual_artist = re.sub(r'\[[^\]]*\]', '', individual_artist).strip()
                    
                    if individual_artist and individual_artist not in all_artists_to_process:
                        all_artists_to_process[individual_artist] = artist_data if isinstance(artist_data, dict) else {}
                
                # Now process each individual artist
                for artist_name in all_artists_to_process:
                    # Skip if we've already processed this artist
                    if artist_name in person_uri_map:
                        continue
                    
                    artist_count += 1
                    
                    # Normalize the artist name for matching
                    normalized_json_artist = self._normalize_artist_name(artist_name)
                    
                    # Check for a matching artist in our normalized index
                    artist_uri = None
                    artist_id = None
                    artist_exists = False
                    
                    if normalized_json_artist in normalized_artist_index:
                        # We have a normalized name match
                        candidates = normalized_artist_index[normalized_json_artist]
                        
                        # Just use the first match for simplicity
                        if candidates:
                            artist_id, artist_uri, _ = candidates[0]
                            artist_exists = True
                            matched_artists += 1
                    
                    # If no match found, try fuzzy matching
                    if not artist_exists:
                        best_match = None
                        best_score = 0
                        
                        for norm_name, candidates in normalized_artist_index.items():
                            # Skip very short names to avoid false positives
                            if len(norm_name) < 3 or len(normalized_json_artist) < 3:
                                continue
                                
                            # Use token sort ratio for better handling of word order differences
                            score = fuzz.token_sort_ratio(normalized_json_artist, norm_name)
                            
                            # Only consider high-confidence matches
                            if score > 85 and score > best_score:
                                best_score = score
                                best_match = candidates[0]  # Take the first candidate
                        
                        if best_match:
                            artist_id, artist_uri, _ = best_match
                            artist_exists = True
                            matched_artists += 1
                    
                    # If still no match, create a new artist
                    if not artist_exists:
                        artist_id = generate_entity_id(artist_name)
                        artist_uri = URIRef(ARTIST_IRI_PATTERN.format(artist_id))
                        new_artists += 1
                        
                        # Create new artist entity
                        self.graph.add((artist_uri, RDF.type, self.mo.MusicArtist))
                        self.graph.add((artist_uri, RDFS.label, Literal(artist_name, lang="en")))
                        self.graph.add((artist_uri, RDFS.comment, Literal(f"Music artist or band named '{artist_name}'.", lang="en")))
                        
                        # Default to unknown gender
                        gender_uri = self.genders.get("unknown")
                        if gender_uri:
                            self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
                    
                    # Store in our dictionaries
                    person_uri_map[artist_name] = artist_uri
                    self.artists[artist_id] = artist_uri
                    
                    # Add additional artist information if available
                    if isinstance(all_artists_to_process[artist_name], dict):
                        if 'legal_name' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['legal_name']:
                            legal_names = all_artists_to_process[artist_name]['legal_name']
                            if isinstance(legal_names, list):
                                for legal_name in legal_names:
                                    if legal_name:
                                        self.graph.add((artist_uri, self.mo.legalName, Literal(legal_name, lang="en")))
                            else:
                                self.graph.add((artist_uri, self.mo.legalName, Literal(legal_names, lang="en")))
                                
                        if 'gender' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['gender']:
                            gender_str = all_artists_to_process[artist_name]['gender'].lower()
                            if gender_str in self.genders:
                                self.graph.add((artist_uri, self.mo.hasGender, self.genders[gender_str]))
                                
                        if 'date_of_birth' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['date_of_birth']:
                            birth_date = all_artists_to_process[artist_name]['date_of_birth']
                            artists_with_dob += 1
                            
                            # Handle incomplete dates (YYYY or YYYY-MM) by appending default month/day values
                            if re.match(r'^\d{4}$', birth_date):  # Just a year
                                birth_date = f"{birth_date}-01-01"  # Use January 1st
                            elif re.match(r'^\d{4}-\d{2}$', birth_date):  # Year and month
                                birth_date = f"{birth_date}-01"  # Use the 1st day of month
                            
                            try:
                                # Only add as XSD.date if it's a valid date format
                                if re.match(r'^\d{4}-\d{2}-\d{2}$', birth_date):
                                    self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(birth_date, datatype=XSD.date)))
                                else:
                                    # Fall back to string literal if not a valid date format
                                    self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(birth_date)))
                            except Exception as e:
                                # If there's any error, fall back to string
                                print(f"Warning: Invalid birth date '{birth_date}', storing as string")
                                self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(birth_date)))
                                
                        if 'country' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['country']:
                            country = all_artists_to_process[artist_name]['country']
                            self.graph.add((artist_uri, self.mo.country, Literal(country, lang="en")))
                            
                        if 'area' in all_artists_to_process[artist_name] and all_artists_to_process[artist_name]['area']:
                            area = all_artists_to_process[artist_name]['area']
                            if area:  # Check if area is not None
                                self.graph.add((artist_uri, self.mo.area, Literal(area, lang="en")))
        
        print(f"Preprocessed {artist_count} artists from JSON data:")
        print(f"  - {matched_artists} matched to existing artists")
        print(f"  - {new_artists} new artists created")
        print(f"  - {artists_with_dob} artists with birth dates")
        return person_uri_map 