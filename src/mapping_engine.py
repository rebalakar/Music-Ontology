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
    def __init__(self):
        self.graph = Graph()
        # Register namespaces
        for prefix, uri in NAMESPACES.items():
            self.graph.bind(prefix, Namespace(uri))
        
        # Initialize namespaces for easier use
        self.mo = Namespace(NAMESPACES['mo'])
        self.ex = Namespace(NAMESPACES['ex'])
        self.time = Namespace(NAMESPACES['time'])
        
        # Add OWL ontology declarations
        self.graph.add((URIRef(NAMESPACES['mo']), RDF.type, OWL.Ontology))
        self.graph.add((URIRef(NAMESPACES['ex']), RDF.type, OWL.Ontology))
        self.graph.add((URIRef(NAMESPACES['time']), RDF.type, OWL.Ontology))
        
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
        
        # Declare all class types as OWL Classes
        self._declare_classes()
        
        # Declare all properties in advance to ensure Protégé compatibility
        self._declare_properties()
        
        # Initialize common entities
        self._initialize_common_entities()
    
    def _declare_classes(self):
        """Declare all classes as owl:Class with proper subClassOf relationships"""
        classes = [
            self.mo.MusicArtist, self.mo.Track, self.mo.Record, self.mo.Genre, 
            self.mo.Label, self.mo.MusicProducer, self.mo.MusicWriter, self.mo.Arranger,
            self.mo.Language, self.mo.Gender, self.ex.MusicChart, self.ex.ChartEntry,
            self.time.Interval, self.time.Instant, self.time.Duration, self.time.TemporalUnit,
            # Add new classes for the additional roles
            self.mo.Engineer, self.mo.Mixer, self.mo.Vocalist, self.mo.Instrumentalist,
            self.mo.Recorder,
            # Add ChartRun class
            self.ex.ChartRun
        ]
        
        for cls in classes:
            self.graph.add((cls, RDF.type, OWL.Class))
            self.graph.add((cls, RDFS.subClassOf, OWL.Thing))
    
    def _declare_properties(self):
        """Pre-declare all properties as either ObjectProperty or DatatypeProperty"""
        # Object properties
        object_properties = [
            self.mo.hasMusicArtist, self.mo.hasGenre, self.mo.hasWriter, self.mo.hasProducer,
            self.mo.hasArranger, self.mo.hasGender, self.mo.hasLanguage, self.mo.published_as,
            self.mo.forTrack, self.ex.chart, self.ex.inChart, self.ex.hasInterval, 
            self.ex.hasDuration, self.time.hasBeginning, self.time.hasEnd, self.time.unitType,
            self.time.inDate,
            self.mo.hasEngineer,
            self.mo.hasMixer,
            self.mo.hasVocalist,
            self.mo.hasInstrumentalist,
            self.mo.hasRecorder,
            self.mo.hasLabel,
            self.time.before,
            self.time.after,
            self.ex.chartRunDuration,
            self.ex.hasChartRun
        ]
        
        for prop in object_properties:
            self.graph.add((prop, RDF.type, OWL.ObjectProperty))
            # Use the local name directly as the label
            local_name = str(prop).split('#')[-1]
            self.graph.add((prop, RDFS.label, Literal(local_name, lang="en")))
        
        # Datatype properties
        datatype_properties = [
            self.mo.hasLegalName, self.mo.hasLyrics, self.ex.chartPosition, self.time.instantDate,
            self.time.numericDuration, self.time.hasDuration,
            # Add new artist properties
            self.mo.dateOfBirth, self.mo.country, self.mo.area,
            # Add new lyrics properties
            self.mo.hasTranslatedLyrics, self.mo.hasTheme
        ]
        
        for prop in datatype_properties:
            self.graph.add((prop, RDF.type, OWL.DatatypeProperty))
            # Use the local name directly as the label
            local_name = str(prop).split('#')[-1]
            self.graph.add((prop, RDFS.label, Literal(local_name, lang="en")))
    
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
        
        # Initialize language instances
        language_codes = ["eng", "spa", "fra", "deu", "ita", "por", "mul"]
        language_names = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Multiple Languages"]
        
        for code, name in zip(language_codes, language_names):
            language_uri = URIRef(f"{NAMESPACES['mo']}language_{code}")
            self.languages[code] = language_uri
            self.graph.add((language_uri, RDF.type, self.mo.Language))
            self.graph.add((language_uri, RDFS.label, Literal(name, lang="en")))
        
        # Initialize common genres
        common_genres = ["Pop", "Rock", "Hip Hop", "R&B", "Country", "Electronic", "Jazz", "Classical", "Other"]
        for genre in common_genres:
            genre_id = clean_entity_name(genre)
            genre_uri = URIRef(GENRE_IRI_PATTERN.format(genre_id))
            self.genres[genre_id] = genre_uri
            self.graph.add((genre_uri, RDF.type, self.mo.Genre))
            self.graph.add((genre_uri, RDFS.label, Literal(genre, lang="en")))
        
        # Initialize temporal units
        units = ["second", "minute", "hour", "day", "week", "month", "year"]
        for unit in units:
            unit_uri = URIRef(TEMPORAL_UNIT_IRI_PATTERN.format(unit))
            self.temporal_units[unit] = unit_uri
            self.graph.add((unit_uri, RDF.type, self.time.TemporalUnit))
            self.graph.add((unit_uri, RDFS.label, Literal(unit, lang="en")))
        
        # Initialize Billboard Hot 100 chart
        billboard_hot100 = URIRef(CHART_IRI_PATTERN.format('hot_100'))
        self.charts['hot_100'] = billboard_hot100
        self.graph.add((billboard_hot100, RDF.type, self.ex.MusicChart))
        self.graph.add((billboard_hot100, RDFS.label, Literal("Billboard Hot 100", lang="en")))
        
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
        self.graph.add((interval_uri, self.time.hasBeginning, start_instant_uri))
        self.graph.add((interval_uri, self.time.hasEnd, end_instant_uri))
        self.graph.add((interval_uri, RDFS.label, Literal(f"Week of {start_date_str}", lang="en")))
        
        return interval_uri
    
    def _get_or_create_time_instant(self, date_str):
        """Get or create a time instant for a given date"""
        
        if date_str in self.instants:
            return self.instants[date_str]
        
        instant_uri = URIRef(TIME_INSTANT_IRI_PATTERN.format(date_str))
        self.instants[date_str] = instant_uri
        
        self.graph.add((instant_uri, RDF.type, self.time.Instant))
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
        
        # Create the duration
        self.graph.add((duration_uri, RDF.type, self.time.Duration))
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
            artist_name = artist_name.strip()  # Clean up the name
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
    
    def _normalize_track_name(self, track_name):
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
        Uses more advanced matching to handle spelling variations and name format differences.
        """
        if not json_artists or not csv_artist_id:
            return False
            
        # Try to extract artist names from the CSV artist ID
        csv_artists = csv_artist_id.split('_and_')
        if len(csv_artists) == 1:
            # It might be a single artist name with underscores
            csv_artist_name = csv_artist_id.replace('_', ' ')
            csv_artists = [csv_artist_name]
        
        # Normalize all artist names
        normalized_json_artists = [clean_entity_name(a.lower()) for a in json_artists]
        normalized_csv_artists = [clean_entity_name(a.lower()) for a in csv_artists]
        
        # Check for direct matches first
        for json_artist in normalized_json_artists:
            for csv_artist in normalized_csv_artists:
                # Direct match
                if json_artist == csv_artist:
                    return True
                
                # Check if one is a substring of the other (for example "Jay-Z" vs "Jay Z")
                if json_artist in csv_artist or csv_artist in json_artist:
                    return True
                
                # Fuzzy match with a high threshold (85+)
                similarity = fuzz.ratio(json_artist, csv_artist)
                if similarity >= 85:
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
        
        for key, data in json_data.items():
            # Extract track name and process
            track_name = data.get('track', '')
            
            # Extract artist information - we'll use this for better matching
            artists = []
            if 'artist' in data and data['artist']:
                for artist_data in data['artist']:
                    artist_name = artist_data.get('artist_name', '')
                    if artist_name:
                        artists.append(artist_name)
            
            # Generate a consistent ID format that matches the CSV approach
            # Using the first artist if available, or a placeholder if not
            primary_artist = artists[0] if artists else "unknown_artist"
            consistent_track_id = generate_entity_id(f"{track_name}_{primary_artist}")
            
            # Now try multiple matching strategies to find existing track
            track_uri = None
            track_exists = False
            
            # Strategy 1: Direct ID match (most reliable)
            if consistent_track_id in self.tracks:
                track_uri = self.tracks[consistent_track_id]
                track_exists = True
            
            # Strategy 2: Advanced matching using normalized track names and all artists
            if not track_exists:
                normalized_track_name = self._normalize_track_name(track_name)
                
                for existing_id, existing_uri in self.tracks.items():
                    # Parse existing ID to extract name and artist components
                    existing_parts = existing_id.split('_')
                    if len(existing_parts) > 1:
                        # Extract the artist portion (last component)
                        existing_artist = existing_parts[-1]
                        # Everything else is the track name
                        existing_track = '_'.join(existing_parts[:-1])
                        
                        # Apply same normalization to existing track name
                        normalized_existing = self._normalize_track_name(existing_track.replace('_', ' '))
                        
                        # First check: Do normalized track names match exactly?
                        exact_match = normalized_track_name == normalized_existing
                        
                        # Second check: Are they similar enough for fuzzy matching?
                        fuzzy_match = False
                        if len(normalized_track_name) > 3 and len(normalized_existing) > 3:
                            similarity = fuzz.ratio(normalized_track_name, normalized_existing)
                            fuzzy_match = similarity >= 90  # Higher threshold for track names
                        
                        # If either track match and any artist matches, use this entity
                        if (exact_match or fuzzy_match) and self._artists_match(artists, existing_artist):
                            track_uri = existing_uri
                            track_exists = True
                            # Add this ID mapping for future lookups
                            self.tracks[consistent_track_id] = track_uri
                            break
            
            # Strategy 3: Fuzzy fallback for track name only (least strict)
            if not track_exists:
                normalized_track_name = self._normalize_track_name(track_name)
                
                for existing_id, existing_uri in self.tracks.items():
                    existing_parts = existing_id.split('_')
                    if len(existing_parts) > 1:
                        existing_track = '_'.join(existing_parts[:-1]).replace('_', ' ')
                        normalized_existing = self._normalize_track_name(existing_track)
                        
                        # Less strict fuzzy matching as a last resort
                        # (shorter threshold for very short track names)
                        threshold = 85 if len(normalized_track_name) > 10 else 95
                        
                        if len(normalized_track_name) > 3 and len(normalized_existing) > 3:
                            similarity = fuzz.ratio(normalized_track_name, normalized_existing)
                            if similarity >= threshold:
                                track_uri = existing_uri
                                track_exists = True
                                # Add this ID mapping for future lookups
                                self.tracks[consistent_track_id] = track_uri
                                break
            
            # If no match found, skip this JSON track - don't create a new entity
            if not track_exists:
                skipped_tracks += 1
                continue  # Skip to the next JSON track
            
            # Track was found, count it and proceed with enrichment
            matched_tracks += 1
            
            # Add lyrics if available 
            # Check if we're using track ID keys for lyrics instead of JSON keys
            if consistent_track_id in self.lyrics_dict:
                lyrics_text = self.lyrics_dict[consistent_track_id]
                self.graph.add((track_uri, self.mo.hasLyrics, Literal(lyrics_text)))
            
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
            
            # Process record label - new addition
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
            
            # Process artists
            if 'artist' in data and data['artist']:
                for artist_data in data['artist']:
                    artist_name = artist_data.get('artist_name', '')
                    if not artist_name:
                        continue
                    
                    artist_id = generate_entity_id(artist_name)
                    artist_uri = URIRef(ARTIST_IRI_PATTERN.format(artist_id))
                    
                    # Use entity resolution to find matching artist
                    artist_found, matching_uri, matched_id = find_matching_artist(
                        artist_name, artist_id, self.artists
                    )
                    
                    if artist_found:
                        artist_uri = matching_uri
                        # Update our artists map with this alternate ID to help future lookups
                        if artist_id != matched_id:
                            self.artists[artist_id] = matching_uri
                    else:
                        # Create new artist if not found
                        self.artists[artist_id] = artist_uri
                        self.graph.add((artist_uri, RDF.type, self.mo.MusicArtist))
                        self.graph.add((artist_uri, RDFS.label, Literal(artist_name, lang="en")))
                        
                        # Default to unknown gender if not specified
                        gender_uri = self.genders.get("unknown")
                        if gender_uri:
                            self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
                    
                    # Process gender if available - always update this
                    if 'gender' in artist_data and artist_data['gender']:
                        gender = artist_data['gender'].lower()
                        gender_uri = self.genders.get(gender.lower())
                        
                        if gender_uri:
                            # Remove any existing gender before adding the new one
                            for s, p, o in self.graph.triples((artist_uri, self.mo.hasGender, None)):
                                self.graph.remove((s, p, o))
                            self.graph.add((artist_uri, self.mo.hasGender, gender_uri))
                    
                    # Process legal names if available - always add these
                    if 'legal_name' in artist_data and artist_data['legal_name']:
                        for legal_name in artist_data['legal_name']:
                            if legal_name:  # Check if not empty
                                # Check if this legal name is already added
                                legal_name_exists = False
                                for _, _, existing_name in self.graph.triples((artist_uri, self.mo.hasLegalName, None)):
                                    if str(existing_name) == legal_name:
                                        legal_name_exists = True
                                        break
                                
                                if not legal_name_exists:
                                    self.graph.add((artist_uri, self.mo.hasLegalName, Literal(legal_name)))

                    # Add new artist properties - always update if available
                    # Date of birth
                    if 'date_of_birth' in artist_data and artist_data['date_of_birth']:
                        date_of_birth = artist_data['date_of_birth']
                        # Remove any existing date of birth before adding the new one
                        for s, p, o in self.graph.triples((artist_uri, self.mo.dateOfBirth, None)):
                            self.graph.remove((s, p, o))
                        
                        # Validate and normalize the date format
                        validated_date = self._validate_xsd_date(date_of_birth)
                        if validated_date:
                            self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(validated_date, datatype=XSD.date)))
                        else:
                            # Store as string if not valid XSD date format
                            self.graph.add((artist_uri, self.mo.dateOfBirth, Literal(date_of_birth)))
                    
                    # Country
                    if 'country' in artist_data and artist_data['country']:
                        country = artist_data['country']
                        # Remove any existing country before adding the new one
                        for s, p, o in self.graph.triples((artist_uri, self.mo.country, None)):
                            self.graph.remove((s, p, o))
                        self.graph.add((artist_uri, self.mo.country, Literal(country)))
                    
                    # Area (city/region)
                    if 'area' in artist_data and artist_data['area']:
                        area = artist_data['area']
                        # Remove any existing area before adding the new one
                        for s, p, o in self.graph.triples((artist_uri, self.mo.area, None)):
                            self.graph.remove((s, p, o))
                        self.graph.add((artist_uri, self.mo.area, Literal(area)))
                    
                    # Link track to artist
                    self.graph.add((track_uri, self.mo.hasMusicArtist, artist_uri))
            
            # Process writers
            if 'writer' in data and data['writer']:
                for writer_name in data['writer']:
                    if not writer_name:
                        continue
                    
                    writer_id = generate_entity_id(writer_name)
                    writer_uri = URIRef(WRITER_IRI_PATTERN.format(writer_id))
                    
                    if writer_id not in self.writers:
                        self.writers[writer_id] = writer_uri
                    self.graph.add((writer_uri, RDF.type, self.mo.MusicWriter))
                    self.graph.add((writer_uri, RDFS.label, Literal(writer_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasWriter, writer_uri))
            
            # Process composers
            if 'composer' in data and data['composer']:
                for composer_name in data['composer']:
                    if not composer_name:
                        continue
                    
                    composer_id = generate_entity_id(composer_name)
                    composer_uri = URIRef(PRODUCER_IRI_PATTERN.format(composer_id))
                    
                    if composer_id not in self.producers:
                        self.producers[composer_id] = composer_uri
                    self.graph.add((composer_uri, RDF.type, self.mo.MusicProducer))
                    self.graph.add((composer_uri, RDFS.label, Literal(composer_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasProducer, composer_uri))
            
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
                    
                    arranger_id = generate_entity_id(arranger_name)
                    arranger_uri = URIRef(ARRANGER_IRI_PATTERN.format(arranger_id))
                    
                    if arranger_id not in self.arrangers:
                        self.arrangers[arranger_id] = arranger_uri
                        self.graph.add((arranger_uri, RDF.type, self.mo.Arranger))
                        self.graph.add((arranger_uri, RDFS.label, Literal(arranger_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasArranger, arranger_uri))
            
            # Process engineer
            if 'engineer' in data and data['engineer']:
                for engineer_name in data['engineer']:
                    if not engineer_name:
                        continue
                    
                    engineer_id = generate_entity_id(engineer_name)
                    engineer_uri = URIRef(f"{NAMESPACES['mo']}engineer_{engineer_id}")
                    
                    if engineer_id not in self.engineers:
                        self.engineers[engineer_id] = engineer_uri
                        self.graph.add((engineer_uri, RDF.type, self.mo.Engineer))
                        self.graph.add((engineer_uri, RDFS.label, Literal(engineer_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasEngineer, engineer_uri))
            
            # Process mix
            if 'mix' in data and data['mix']:
                for mixer_name in data['mix']:
                    if not mixer_name:
                        continue
                    
                    mixer_id = generate_entity_id(mixer_name)
                    mixer_uri = URIRef(f"{NAMESPACES['mo']}mixer_{mixer_id}")
                    
                    if mixer_id not in self.mixers:
                        self.mixers[mixer_id] = mixer_uri
                        self.graph.add((mixer_uri, RDF.type, self.mo.Mixer))
                        self.graph.add((mixer_uri, RDFS.label, Literal(mixer_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasMixer, mixer_uri))
            
            # Process vocalist
            if 'vocal' in data and data['vocal']:
                for vocalist_name in data['vocal']:
                    if not vocalist_name:
                        continue
                    
                    vocalist_id = generate_entity_id(vocalist_name)
                    vocalist_uri = URIRef(f"{NAMESPACES['mo']}vocalist_{vocalist_id}")
                    
                    if vocalist_id not in self.vocalists:
                        self.vocalists[vocalist_id] = vocalist_uri
                        self.graph.add((vocalist_uri, RDF.type, self.mo.Vocalist))
                        self.graph.add((vocalist_uri, RDFS.label, Literal(vocalist_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasVocalist, vocalist_uri))
            
            # Process instrumentalist
            if 'instrument' in data and data['instrument']:
                for instrumentalist_name in data['instrument']:
                    if not instrumentalist_name:
                        continue
                    
                    instrumentalist_id = generate_entity_id(instrumentalist_name)
                    instrumentalist_uri = URIRef(f"{NAMESPACES['mo']}instrumentalist_{instrumentalist_id}")
                    
                    if instrumentalist_id not in self.instrumentalists:
                        self.instrumentalists[instrumentalist_id] = instrumentalist_uri
                        self.graph.add((instrumentalist_uri, RDF.type, self.mo.Instrumentalist))
                        self.graph.add((instrumentalist_uri, RDFS.label, Literal(instrumentalist_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasInstrumentalist, instrumentalist_uri))
            
            # Process recorder
            if 'recording' in data and data['recording']:
                for recorder_name in data['recording']:
                    if not recorder_name:
                        continue
                    
                    recorder_id = generate_entity_id(recorder_name)
                    recorder_uri = URIRef(f"{NAMESPACES['mo']}recorder_{recorder_id}")
                    
                    if recorder_id not in self.recorders:
                        self.recorders[recorder_id] = recorder_uri
                        self.graph.add((recorder_uri, RDF.type, self.mo.Recorder))
                        self.graph.add((recorder_uri, RDFS.label, Literal(recorder_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasRecorder, recorder_uri))
            
            # Process producer if not handled by composer mapping
            if 'producer' in data and data['producer']:
                for producer_name in data['producer']:
                    if not producer_name:
                        continue
                    
                    producer_id = generate_entity_id(producer_name)
                    producer_uri = URIRef(PRODUCER_IRI_PATTERN.format(producer_id))
                    
                    if producer_id not in self.producers:
                        self.producers[producer_id] = producer_uri
                        self.graph.add((producer_uri, RDF.type, self.mo.MusicProducer))
                        self.graph.add((producer_uri, RDFS.label, Literal(producer_name, lang="en")))
                    
                    self.graph.add((track_uri, self.mo.hasProducer, producer_uri))
    
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