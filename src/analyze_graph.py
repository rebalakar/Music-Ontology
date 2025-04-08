#!/usr/bin/env python
import rdflib
from rdflib import Namespace, URIRef
import os
import sys
from collections import defaultdict
import pandas as pd
import numpy as np
import re
from datetime import datetime

# Add the current directory to sys.path for local imports
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Import config for namespaces
from config import NAMESPACES, OUTPUT_PATH

def load_graph(file_path):
    """Load the RDF graph from the Turtle file"""
    g = rdflib.Graph()
    g.parse(file_path, format='turtle')
    return g

def count_entity_types(graph):
    """Count instances of each class type in the graph"""
    mo = Namespace(NAMESPACES['mo'])
    ex = Namespace(NAMESPACES['ex'])
    time = Namespace(NAMESPACES['time'])
    
    class_counts = defaultdict(int)
    
    # List all classes from our ontologies
    classes = [
        # Music Ontology
        (mo.MusicArtist, "Music Artists"),
        (mo.Track, "Tracks"),
        (mo.Record, "Records"),
        (mo.Genre, "Genres"),
        (mo.Label, "Labels"),
        (mo.MusicProducer, "Music Producers"),
        (mo.MusicWriter, "Music Writers"),
        (mo.Arranger, "Arrangers"),
        (mo.Language, "Languages"),
        (mo.Gender, "Genders"),
        # Additional roles
        (mo.Engineer, "Engineers"),
        (mo.Mixer, "Mixers"),
        (mo.Vocalist, "Vocalists"),
        (mo.Instrumentalist, "Instrumentalists"),
        (mo.Recorder, "Recorders"),
        
        # Billboard Ontology
        (ex.MusicChart, "Music Charts"),
        (ex.ChartEntry, "Chart Entries"),
        
        # Time Ontology
        (time.Instant, "Time Instants"),
        (time.Interval, "Time Intervals"),
        (time.Duration, "Time Durations"),
        (time.TemporalUnit, "Temporal Units")
    ]
    
    # Count instances of each class
    for class_uri, class_name in classes:
        query = f"""
        SELECT (COUNT(?s) as ?count)
        WHERE {{
            ?s a <{class_uri}> .
        }}
        """
        for row in graph.query(query):
            class_counts[class_name] = int(row[0])
    
    return class_counts

def count_relationship_types(graph):
    """Count usage of each property type in the graph"""
    mo = Namespace(NAMESPACES['mo'])
    ex = Namespace(NAMESPACES['ex'])
    time = Namespace(NAMESPACES['time'])
    
    property_counts = defaultdict(int)
    
    # List all properties from our ontologies
    properties = [
        # Music Ontology
        (mo.hasMusicArtist, "track-artist links"),
        (mo.hasWriter, "track-writer links"),
        (mo.hasProducer, "track-producer links"),
        (mo.hasArranger, "track-arranger links"),
        (mo.hasGenre, "track-genre links"),
        (mo.hasLanguage, "track-language links"),
        (mo.hasLabel, "track-label links"),
        (mo.hasGender, "artist-gender links"),
        (mo.hasLegalName, "artist-legal name links"),
        (mo.published_as, "track-record links"),
        (mo.hasLyrics, "track-lyrics links"),
        # New artist-specific properties
        (mo.dateOfBirth, "artist-birth date links"),
        (mo.country, "artist-country links"),
        (mo.area, "artist-area links"),
        # New relationships for additional roles
        (mo.hasEngineer, "track-engineer links"),
        (mo.hasMixer, "track-mixer links"),
        (mo.hasVocalist, "track-vocalist links"),
        (mo.hasInstrumentalist, "track-instrumentalist links"),
        (mo.hasRecorder, "track-recorder links"),
        
        # Billboard Ontology
        (ex.chart, "chart entry-chart links"),
        (ex.inChart, "chart entry-chart links (alt)"),
        (ex.chartPosition, "chart entry-position links"),
        (mo.forTrack, "chart entry-track links"),
        (ex.hasInterval, "chart entry-interval links"),
        (ex.hasDuration, "chart entry-duration links"),
        
        # Time Ontology
        (time.inDate, "entity-instant links"),
        (time.instantDate, "instant-date links"),
        (time.hasBeginning, "interval-start links"),
        (time.hasEnd, "interval-end links"),
        (time.unitType, "duration-unit links"),
        (time.numericDuration, "duration-value links"),
        (time.hasDuration, "duration-xsd links"),
        (time.before, "instant-before-instant links"),
        (time.after, "instant-after-instant links")
    ]
    
    # Count usage of each property
    for prop_uri, prop_name in properties:
        query = f"""
        SELECT (COUNT(?s) as ?count)
        WHERE {{
            ?s <{prop_uri}> ?o .
        }}
        """
        for row in graph.query(query):
            property_counts[prop_name] = int(row[0])
    
    return property_counts

def analyze_time_relationships(graph):
    """Analyze time-related relationships in the graph"""
    time = Namespace(NAMESPACES['time'])
    
    # Count how many intervals have both beginning and end
    query_complete_intervals = """
    SELECT (COUNT(?interval) as ?count)
    WHERE {
        ?interval a <http://example.org/time#Interval> .
        ?interval <http://example.org/time#hasBeginning> ?start .
        ?interval <http://example.org/time#hasEnd> ?end .
    }
    """
    
    complete_intervals = 0
    for row in graph.query(query_complete_intervals):
        complete_intervals = int(row[0])
    
    # Check temporal relationships between instants
    query_before_relations = """
    SELECT (COUNT(?s) as ?count)
    WHERE {
        ?s <http://example.org/time#before> ?o .
    }
    """
    
    query_after_relations = """
    SELECT (COUNT(?s) as ?count)
    WHERE {
        ?s <http://example.org/time#after> ?o .
    }
    """
    
    before_relations = 0
    for row in graph.query(query_before_relations):
        before_relations = int(row[0])
        
    after_relations = 0
    for row in graph.query(query_after_relations):
        after_relations = int(row[0])
        
    return {
        "Complete intervals (with beginning and end)": complete_intervals,
        "time:before relationships": before_relations,
        "time:after relationships": after_relations,
        "Total temporal relationships": before_relations + after_relations
    }

def analyze_lyrics(graph):
    """Analyze lyrics data in the knowledge graph"""
    mo = Namespace(NAMESPACES['mo'])
    
    # Count tracks with lyrics
    query_tracks_with_lyrics = """
    SELECT (COUNT(DISTINCT ?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasLyrics> ?lyrics .
    }
    """
    
    tracks_with_lyrics = 0
    for row in graph.query(query_tracks_with_lyrics):
        tracks_with_lyrics = int(row[0])
    
    # Count total tracks
    query_total_tracks = """
    SELECT (COUNT(?track) as ?count)
    WHERE {
        ?track a <http://example.org/mo#Track> .
    }
    """
    
    total_tracks = 0
    for row in graph.query(query_total_tracks):
        total_tracks = int(row[0])
    
    # Calculate coverage percentage
    lyrics_coverage = 0
    if total_tracks > 0:
        lyrics_coverage = (tracks_with_lyrics / total_tracks) * 100
    
    # Count tracks with language information
    query_tracks_with_language = """
    SELECT (COUNT(DISTINCT ?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasLanguage> ?language .
    }
    """
    
    tracks_with_language = 0
    for row in graph.query(query_tracks_with_language):
        tracks_with_language = int(row[0])
    
    # Count tracks with translated lyrics
    query_tracks_with_translations = """
    SELECT (COUNT(DISTINCT ?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasTranslatedLyrics> ?translated .
    }
    """
    
    tracks_with_translations = 0
    for row in graph.query(query_tracks_with_translations):
        tracks_with_translations = int(row[0])
    
    # Count tracks with theme information
    query_tracks_with_themes = """
    SELECT (COUNT(DISTINCT ?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasTheme> ?theme .
    }
    """
    
    tracks_with_themes = 0
    for row in graph.query(query_tracks_with_themes):
        tracks_with_themes = int(row[0])
    
    # Get theme distribution
    query_theme_distribution = """
    SELECT ?theme (COUNT(?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasTheme> ?theme .
    }
    GROUP BY ?theme
    ORDER BY DESC(?count)
    LIMIT 10
    """
    
    theme_distribution = []
    total_themes = 0
    
    for row in graph.query(query_theme_distribution):
        theme = str(row[0])
        count = int(row[1])
        total_themes += count
        theme_distribution.append((theme, count))
    
    # Get language distribution
    query_language_distribution = """
    SELECT ?language (COUNT(?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasLanguage> ?language .
        ?language rdfs:label ?label .
    }
    GROUP BY ?language ?label
    ORDER BY DESC(?count)
    """
    
    language_distribution = []
    total_with_language = 0
    
    for row in graph.query(query_language_distribution):
        language_uri = row[0]
        count = int(row[1])
        total_with_language += count
        
        # Get the label for the language
        label_query = f"""
        SELECT ?label
        WHERE {{
            <{language_uri}> rdfs:label ?label .
        }}
        LIMIT 1
        """
        
        language_label = ""
        for label_row in graph.query(label_query):
            language_label = str(label_row[0])
        
        language_distribution.append((language_label, count))
    
    # Get sample lyrics to analyze length distribution
    query_lyrics_sample = """
    SELECT ?lyrics
    WHERE {
        ?track <http://example.org/mo#hasLyrics> ?lyrics .
    }
    LIMIT 1000
    """
    
    lyrics_lengths = []
    lyrics_lines = []
    
    for row in graph.query(query_lyrics_sample):
        lyrics_text = str(row[0])
        lyrics_lengths.append(len(lyrics_text))
        
        # Count number of lines
        lines = lyrics_text.count('\n') + 1
        lyrics_lines.append(lines)
    
    # Calculate statistics from samples
    avg_lyrics_length = 0
    median_lyrics_length = 0
    avg_lines = 0
    
    if lyrics_lengths:
        avg_lyrics_length = sum(lyrics_lengths) / len(lyrics_lengths)
        median_lyrics_length = sorted(lyrics_lengths)[len(lyrics_lengths) // 2]
        avg_lines = sum(lyrics_lines) / len(lyrics_lines)
    
    # Calculate lyrics character distribution
    length_bins = [(0, 1000), (1000, 5000), (5000, 10000), (10000, float('inf'))]
    length_distribution = []
    
    for min_len, max_len in length_bins:
        count = sum(1 for length in lyrics_lengths if min_len <= length < max_len)
        percentage = (count / len(lyrics_lengths)) * 100 if lyrics_lengths else 0
        length_distribution.append({
            'range': f"{min_len}-{max_len if max_len != float('inf') else 'inf'} chars",
            'count': count,
            'percentage': percentage
        })
    
    # Format theme distribution for output
    formatted_theme_dist = []
    if theme_distribution and total_themes > 0:
        for theme, count in theme_distribution:
            percentage = (count / total_themes) * 100
            formatted_theme_dist.append({
                'theme': theme,
                'count': count,
                'percentage': percentage
            })
    
    # Format language distribution for output
    formatted_lang_dist = []
    if language_distribution and total_with_language > 0:
        for lang, count in language_distribution:
            percentage = (count / total_with_language) * 100
            formatted_lang_dist.append({
                'language': lang,
                'count': count,
                'percentage': percentage
            })
    
    return {
        "Tracks with lyrics": tracks_with_lyrics,
        "Total tracks": total_tracks,
        "Lyrics coverage (%)": lyrics_coverage,
        "Tracks with language info": tracks_with_language,
        "Language coverage (%)": (tracks_with_language / total_tracks) * 100 if total_tracks > 0 else 0,
        "Tracks with translated lyrics": tracks_with_translations,
        "Translation coverage (%)": (tracks_with_translations / total_tracks) * 100 if total_tracks > 0 else 0,
        "Tracks with theme info": tracks_with_themes,
        "Theme coverage (%)": (tracks_with_themes / total_tracks) * 100 if total_tracks > 0 else 0,
        "Average lyrics length (chars)": avg_lyrics_length,
        "Median lyrics length (chars)": median_lyrics_length,
        "Average lines per lyrics": avg_lines,
        "Lyrics length distribution": length_distribution,
        "Theme distribution": formatted_theme_dist,
        "Language distribution": formatted_lang_dist
    }

def analyze_additional_roles(graph):
    """Analyze the new roles added to the knowledge graph"""
    mo = Namespace(NAMESPACES['mo'])
    
    # Define the roles to analyze
    roles = [
        ('Engineer', mo.hasEngineer),
        ('Mixer', mo.hasMixer),
        ('Vocalist', mo.hasVocalist),
        ('Instrumentalist', mo.hasInstrumentalist),
        ('Recorder', mo.hasRecorder)
    ]
    
    results = {}
    
    # Count total tracks
    query_total_tracks = """
    SELECT (COUNT(?track) as ?count)
    WHERE {
        ?track a <http://example.org/mo#Track> .
    }
    """
    
    total_tracks = 0
    for row in graph.query(query_total_tracks):
        total_tracks = int(row[0])
    
    # For each role, count tracks with that role
    for role_name, role_property in roles:
        query = f"""
        SELECT (COUNT(DISTINCT ?track) as ?count)
        WHERE {{
            ?track <{role_property}> ?person .
        }}
        """
        
        count = 0
        for row in graph.query(query):
            count = int(row[0])
        
        coverage = 0
        if total_tracks > 0:
            coverage = (count / total_tracks) * 100
        
        results[f"Tracks with {role_name}"] = count
        results[f"{role_name} coverage (%)"] = coverage
    
    return results

def analyze_artists(graph):
    """Analyze artist data including birth date, country and area information"""
    mo = Namespace(NAMESPACES['mo'])
    
    # Count total artists
    query_total_artists = """
    SELECT (COUNT(?artist) as ?count)
    WHERE {
        ?artist a <http://example.org/mo#MusicArtist> .
    }
    """
    
    total_artists = 0
    for row in graph.query(query_total_artists):
        total_artists = int(row[0])
    
    # Count artists with date of birth
    query_artists_with_dob = """
    SELECT (COUNT(DISTINCT ?artist) as ?count)
    WHERE {
        ?artist a <http://example.org/mo#MusicArtist> .
        ?artist <http://example.org/mo#dateOfBirth> ?dob .
    }
    """
    
    artists_with_dob = 0
    for row in graph.query(query_artists_with_dob):
        artists_with_dob = int(row[0])
    
    # Count artists with country information
    query_artists_with_country = """
    SELECT (COUNT(DISTINCT ?artist) as ?count)
    WHERE {
        ?artist a <http://example.org/mo#MusicArtist> .
        ?artist <http://example.org/mo#country> ?country .
    }
    """
    
    artists_with_country = 0
    for row in graph.query(query_artists_with_country):
        artists_with_country = int(row[0])
    
    # Count artists with area information
    query_artists_with_area = """
    SELECT (COUNT(DISTINCT ?artist) as ?count)
    WHERE {
        ?artist a <http://example.org/mo#MusicArtist> .
        ?artist <http://example.org/mo#area> ?area .
    }
    """
    
    artists_with_area = 0
    for row in graph.query(query_artists_with_area):
        artists_with_area = int(row[0])
    
    # Count the distribution of artist countries (top 10)
    query_country_distribution = """
    SELECT ?country (COUNT(?artist) as ?count)
    WHERE {
        ?artist a <http://example.org/mo#MusicArtist> .
        ?artist <http://example.org/mo#country> ?country .
    }
    GROUP BY ?country
    ORDER BY DESC(?count)
    LIMIT 10
    """
    
    country_distribution = []
    for row in graph.query(query_country_distribution):
        country = str(row[0])
        count = int(row[1])
        percentage = (count / artists_with_country) * 100 if artists_with_country > 0 else 0
        country_distribution.append({
            'country': country,
            'count': count,
            'percentage': percentage
        })
    
    # Calculate decade of birth distribution (if date of birth available)
    query_dob_sample = """
    SELECT ?dob
    WHERE {
        ?artist a <http://example.org/mo#MusicArtist> .
        ?artist <http://example.org/mo#dateOfBirth> ?dob .
    }
    """
    
    birth_decades = defaultdict(int)
    for row in graph.query(query_dob_sample):
        try:
            dob = str(row[0])
            # Extract the year and calculate the decade
            year = int(dob.split('-')[0])
            decade = (year // 10) * 10
            birth_decades[f"{decade}s"] += 1
        except (ValueError, IndexError):
            # Skip malformed dates
            continue
    
    # Format decade distribution
    decade_distribution = []
    for decade, count in sorted(birth_decades.items()):
        percentage = (count / artists_with_dob) * 100 if artists_with_dob > 0 else 0
        decade_distribution.append({
            'decade': decade,
            'count': count,
            'percentage': percentage
        })
    
    return {
        "Total artists": total_artists,
        "Artists with birth date": artists_with_dob,
        "Birth date coverage (%)": (artists_with_dob / total_artists) * 100 if total_artists > 0 else 0,
        "Artists with country": artists_with_country,
        "Country coverage (%)": (artists_with_country / total_artists) * 100 if total_artists > 0 else 0,
        "Artists with area": artists_with_area,
        "Area coverage (%)": (artists_with_area / total_artists) * 100 if total_artists > 0 else 0,
        "Country distribution": country_distribution,
        "Birth decade distribution": decade_distribution
    }

def analyze_labels(graph):
    """Analyze record label information"""
    mo = Namespace(NAMESPACES['mo'])
    
    # Count total labels
    query_total_labels = """
    SELECT (COUNT(?label) as ?count)
    WHERE {
        ?label a <http://example.org/mo#Label> .
    }
    """
    
    total_labels = 0
    for row in graph.query(query_total_labels):
        total_labels = int(row[0])
    
    # Count tracks with label information
    query_tracks_with_label = """
    SELECT (COUNT(DISTINCT ?track) as ?count)
    WHERE {
        ?track a <http://example.org/mo#Track> .
        ?track <http://example.org/mo#hasLabel> ?label .
    }
    """
    
    tracks_with_label = 0
    for row in graph.query(query_tracks_with_label):
        tracks_with_label = int(row[0])
    
    # Count total tracks
    query_total_tracks = """
    SELECT (COUNT(?track) as ?count)
    WHERE {
        ?track a <http://example.org/mo#Track> .
    }
    """
    
    total_tracks = 0
    for row in graph.query(query_total_tracks):
        total_tracks = int(row[0])
    
    # Calculate label coverage
    label_coverage = (tracks_with_label / total_tracks) * 100 if total_tracks > 0 else 0
    
    # Get top 10 labels by track count
    query_top_labels = """
    SELECT ?label_name (COUNT(?track) as ?count)
    WHERE {
        ?track <http://example.org/mo#hasLabel> ?label .
        ?label <http://www.w3.org/2000/01/rdf-schema#label> ?label_name .
    }
    GROUP BY ?label_name
    ORDER BY DESC(?count)
    LIMIT 10
    """
    
    top_labels = []
    for row in graph.query(query_top_labels):
        label_name = str(row[0])
        count = int(row[1])
        percentage = (count / tracks_with_label) * 100 if tracks_with_label > 0 else 0
        top_labels.append({
            'label': label_name,
            'tracks': count,
            'percentage': percentage
        })
    
    return {
        "Total record labels": total_labels,
        "Tracks with label": tracks_with_label,
        "Total tracks": total_tracks,
        "Label coverage (%)": label_coverage,
        "Top labels": top_labels
    }

def analyze_chart_runs(graph):
    """Analyze chart runs and their durations"""
    ex = Namespace(NAMESPACES['ex'])
    mo = Namespace(NAMESPACES['mo'])
    
    # Count the number of chart runs
    query_chart_runs = """
    SELECT (COUNT(?run) as ?count)
    WHERE {
        ?run a <http://example.org/billboard#ChartRun> .
    }
    """
    
    total_chart_runs = 0
    for row in graph.query(query_chart_runs):
        total_chart_runs = int(row[0])
    
    # Get distribution of chart run durations (in days)
    query_chart_durations = """
    SELECT ?run ?duration ?unit
    WHERE {
        ?run a <http://example.org/billboard#ChartRun> .
        ?run <http://example.org/billboard#chartRunDuration> ?durEntity .
        ?durEntity <http://example.org/time#numericDuration> ?duration .
        ?durEntity <http://example.org/time#unitType> ?unitType .
        ?unitType rdfs:label ?unit .
    }
    """
    
    durations = []
    for row in graph.query(query_chart_durations):
        duration = float(row[1])
        unit = str(row[2])
        # If the duration is in days, convert to weeks for consistency
        if unit == "day":
            duration = duration / 7
        durations.append(duration)
    
    # Calculate statistics
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        # Already in weeks, no need to convert
        avg_duration_weeks = avg_duration
        max_duration_weeks = max_duration
        min_duration_weeks = min_duration
    else:
        avg_duration = 0
        max_duration = 0
        min_duration = 0
        avg_duration_weeks = 0
        max_duration_weeks = 0
        min_duration_weeks = 0
    
    # Create duration brackets for histogram
    if durations:
        buckets = [
            {"range": "< 1 week", "min": 0, "max": 0.99, "count": 0},
            {"range": "1 week", "min": 1, "max": 1.99, "count": 0},
            {"range": "2 weeks", "min": 2, "max": 2.99, "count": 0},
            {"range": "3-4 weeks", "min": 3, "max": 4.99, "count": 0},
            {"range": "5-8 weeks", "min": 5, "max": 8.99, "count": 0},
            {"range": "9-12 weeks", "min": 9, "max": 12.99, "count": 0},
            {"range": "13-26 weeks", "min": 13, "max": 26.99, "count": 0},
            {"range": "> 26 weeks", "min": 27, "max": 9999, "count": 0}
        ]
        
        for duration in durations:
            for bucket in buckets:
                if bucket["min"] <= duration <= bucket["max"]:
                    bucket["count"] += 1
                    break
        
        # Calculate percentages
        for bucket in buckets:
            bucket["percentage"] = (bucket["count"] / len(durations)) * 100
    else:
        buckets = []
    
    # Count tracks with multiple chart runs
    query_tracks_with_runs = """
    SELECT ?track (COUNT(?run) as ?runCount)
    WHERE {
        ?run a <http://example.org/billboard#ChartRun> .
        ?run <http://example.org/mo#forTrack> ?track .
    }
    GROUP BY ?track
    """
    
    tracks_with_multiple_runs = 0
    total_tracks_with_runs = 0
    run_counts = []
    
    for row in graph.query(query_tracks_with_runs):
        total_tracks_with_runs += 1
        run_count = int(row[1])
        run_counts.append(run_count)
        if run_count > 1:
            tracks_with_multiple_runs += 1
    
    # Calculate percentage of tracks with multiple runs
    multiple_runs_pct = 0
    if total_tracks_with_runs > 0:
        multiple_runs_pct = (tracks_with_multiple_runs / total_tracks_with_runs) * 100
    
    # Calculate average runs per track
    avg_runs_per_track = 0
    if run_counts:
        avg_runs_per_track = sum(run_counts) / len(run_counts)
    
    # Find longest continuous chart run (not just any run)
    query_top_continuous_runs = """
    SELECT ?track ?trackName ?duration ?unit
    WHERE {
        ?run a <http://example.org/billboard#ChartRun> .
        ?run <http://example.org/mo#forTrack> ?track .
        ?track rdfs:label ?trackName .
        ?run <http://example.org/billboard#chartRunDuration> ?durEntity .
        ?durEntity <http://example.org/time#numericDuration> ?duration .
        ?durEntity <http://example.org/time#unitType> ?unitType .
        ?unitType rdfs:label ?unit .
    }
    ORDER BY DESC(?duration)
    LIMIT 10
    """
    
    top_continuous_runs = []
    for row in graph.query(query_top_continuous_runs):
        track_uri = str(row[0])
        track_name = str(row[1])
        duration = float(row[2])
        unit = str(row[3])
        
        # If the duration is in days, convert to weeks
        weeks_duration = duration
        if unit == "day":
            weeks_duration = duration / 7
        
        # Get artist for this track
        query_artist = f"""
        SELECT ?artistName
        WHERE {{
            <{track_uri}> <http://example.org/mo#hasMusicArtist> ?artist .
            ?artist rdfs:label ?artistName .
        }}
        LIMIT 1
        """
        
        artist_name = "Unknown Artist"
        for artist_row in graph.query(query_artist):
            artist_name = str(artist_row[0])
        
        top_continuous_runs.append({
            "track": track_name,
            "artist": artist_name,
            "duration_weeks": round(weeks_duration, 1)
        })
    
    # Find tracks with most total weeks on chart (combined from all runs)
    query_most_weeks_total = """
    SELECT ?track ?trackName (SUM(?adjustedDuration) as ?totalDuration)
    WHERE {
        ?run a <http://example.org/billboard#ChartRun> .
        ?run <http://example.org/mo#forTrack> ?track .
        ?track rdfs:label ?trackName .
        ?run <http://example.org/billboard#chartRunDuration> ?durEntity .
        ?durEntity <http://example.org/time#numericDuration> ?duration .
        ?durEntity <http://example.org/time#unitType> ?unitType .
        ?unitType rdfs:label ?unit .
        BIND(IF(?unit = "day", ?duration / 7, ?duration) AS ?adjustedDuration)
    }
    GROUP BY ?track ?trackName
    ORDER BY DESC(?totalDuration)
    LIMIT 10
    """
    
    most_total_weeks = []
    for row in graph.query(query_most_weeks_total):
        track_uri = str(row[0])
        track_name = str(row[1])
        total_weeks = float(row[2])
        
        # Get artist and count of runs for this track
        query_artist_and_runs = f"""
        SELECT ?artistName (COUNT(?run) as ?runCount)
        WHERE {{
            <{track_uri}> <http://example.org/mo#hasMusicArtist> ?artist .
            ?artist rdfs:label ?artistName .
            ?run a <http://example.org/billboard#ChartRun> .
            ?run <http://example.org/mo#forTrack> <{track_uri}> .
        }}
        GROUP BY ?artistName
        LIMIT 1
        """
        
        artist_name = "Unknown Artist"
        run_count = 0
        for detail_row in graph.query(query_artist_and_runs):
            artist_name = str(detail_row[0])
            run_count = int(detail_row[1])
        
        most_total_weeks.append({
            "track": track_name,
            "artist": artist_name,
            "total_weeks": round(total_weeks, 1),
            "chart_runs": run_count
        })
    
    return {
        "Total chart runs": total_chart_runs,
        "Tracks with chart runs": total_tracks_with_runs,
        "Tracks with multiple chart runs": tracks_with_multiple_runs,
        "Percentage with multiple runs": round(multiple_runs_pct, 1),
        "Average runs per track": round(avg_runs_per_track, 2),
        "Average chart run (weeks)": round(avg_duration_weeks, 1),
        "Longest continuous chart run (weeks)": round(max_duration_weeks, 1),
        "Shortest chart run (weeks)": round(min_duration_weeks, 1),
        "Chart run distribution": buckets,
        "Top 10 longest continuous chart runs": top_continuous_runs,
        "Top 10 tracks by total weeks on chart": most_total_weeks
    }

def generate_comprehensive_report(output_dir, total_triples, entity_counts, relationship_counts, 
                                 time_analysis, lyrics_analysis, roles_analysis,
                                 artist_analysis, label_analysis,
                                 chart_runs_analysis, time_entities_total, time_rels_total):
    """Generate a comprehensive report containing all analysis in a single Markdown file"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create report
    report = f"""# Knowledge Graph Analysis Report

## Overview
| Metric | Value |
|--------|-------|
| Total triples | {total_triples} |
| Entities | {sum(entity_counts.values())} |
| Relationships | {sum(relationship_counts.values())} |

## Entity Types
| Type | Count |
|------|-------|
"""
    
    # Add entity types
    for entity_type, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"| {entity_type} | {count} |\n"
    
    report += f"""
## Relationship Types
| Type | Count |
|------|-------|
"""
    
    # Add relationship types
    for rel_type, count in sorted(relationship_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"| {rel_type} | {count} |\n"
    
    report += f"""
## Time Ontology Analysis
| Metric | Value |
|--------|-------|
"""
    
    for metric, value in time_analysis.items():
        report += f"| {metric} | {value} |\n"
    
    report += f"""
## Chart Runs Analysis
| Metric | Value |
|--------|-------|
"""
    
    for metric, value in chart_runs_analysis.items():
        if metric not in ["Chart run distribution", "Top 10 longest charting songs"]:
            report += f"| {metric} | {value} |\n"
    
    # Add chart run distribution
    if "Chart run distribution" in chart_runs_analysis and chart_runs_analysis["Chart run distribution"]:
        report += f"""
### Chart Run Duration Distribution
| Duration | Count | Percentage |
|----------|-------|------------|
"""
        
        for bucket in chart_runs_analysis["Chart run distribution"]:
            report += f"| {bucket['range']} | {bucket['count']} | {bucket['percentage']:.2f}% |\n"
    
    # Add top songs
    if "Top 10 longest charting songs" in chart_runs_analysis and chart_runs_analysis["Top 10 longest charting songs"]:
        report += f"""
### Top 10 Longest Charting Songs
| Track | Artist | Weeks |
|-------|--------|-------|
"""
        
        for song in chart_runs_analysis["Top 10 longest charting songs"]:
            report += f"| {song['track']} | {song['artist']} | {song['duration_weeks']} |\n"
    
    # Add top longest continuous runs
    if "Top 10 longest continuous chart runs" in chart_runs_analysis and chart_runs_analysis["Top 10 longest continuous chart runs"]:
        report += f"""
### Top 10 Longest Continuous Chart Runs
| Track | Artist | Weeks |
|-------|--------|-------|
"""
        
        for song in chart_runs_analysis["Top 10 longest continuous chart runs"]:
            report += f"| {song['track']} | {song['artist']} | {song['duration_weeks']} |\n"
    
    # Add tracks with most total weeks
    if "Top 10 tracks by total weeks on chart" in chart_runs_analysis and chart_runs_analysis["Top 10 tracks by total weeks on chart"]:
        report += f"""
### Top 10 Tracks by Total Weeks on Chart
| Track | Artist | Total Weeks | Chart Runs |
|-------|--------|-------------|------------|
"""
        
        for song in chart_runs_analysis["Top 10 tracks by total weeks on chart"]:
            report += f"| {song['track']} | {song['artist']} | {song['total_weeks']} | {song['chart_runs']} |\n"
    
    report += f"""
## Lyrics Analysis
| Metric | Value |
|--------|-------|
"""
    
    for metric, value in lyrics_analysis.items():
        if metric not in ["Lyrics length distribution", "Theme distribution", "Language distribution"]:
            report += f"| {metric} | {value} |\n"
    
    # Add lyrics length distribution
    report += f"""
### Lyrics Length Distribution
| Range | Count | Percentage |
|-------|-------|------------|
"""
    
    for entry in lyrics_analysis.get("Lyrics length distribution", []):
        report += f"| {entry['range']} | {entry['count']} | {entry['percentage']:.2f}% |\n"
    
    # Add theme distribution
    if "Theme distribution" in lyrics_analysis and lyrics_analysis["Theme distribution"]:
        report += f"""
### Theme Distribution
| Theme | Count | Percentage |
|-------|-------|------------|
"""
        
        for entry in lyrics_analysis.get("Theme distribution", []):
            report += f"| {entry['theme']} | {entry['count']} | {entry['percentage']:.2f}% |\n"
    
    # Add language distribution
    if "Language distribution" in lyrics_analysis and lyrics_analysis["Language distribution"]:
        report += f"""
### Language Distribution
| Language | Count | Percentage |
|----------|-------|------------|
"""
        
        for entry in lyrics_analysis.get("Language distribution", []):
            report += f"| {entry['language']} | {entry['count']} | {entry['percentage']:.2f}% |\n"
    
    # Add additional roles analysis
    report += f"""
## Additional Roles Analysis
| Role | Tracks | Coverage |
|------|--------|----------|
"""
    
    for i in range(0, len(roles_analysis), 2):
        if i+1 < len(roles_analysis):
            metric_tracks = list(roles_analysis.keys())[i]
            metric_coverage = list(roles_analysis.keys())[i+1]
            role_name = metric_tracks.replace("Tracks with ", "")
            tracks = roles_analysis[metric_tracks]
            coverage = roles_analysis[metric_coverage]
            report += f"| {role_name} | {tracks} | {coverage:.2f}% |\n"
    
    # Add artist analysis
    report += f"""
## Artist Analysis
| Metric | Value |
|--------|-------|
"""
    
    for metric, value in artist_analysis.items():
        if metric not in ["Country distribution", "Birth decade distribution"]:
            if isinstance(value, float):
                report += f"| {metric} | {value:.2f}% |\n"
            else:
                report += f"| {metric} | {value} |\n"
    
    # Add country distribution
    report += f"""
### Artist Country Distribution
| Country | Count | Percentage |
|---------|-------|------------|
"""
    
    for entry in artist_analysis.get("Country distribution", []):
        report += f"| {entry['country']} | {entry['count']} | {entry['percentage']:.2f}% |\n"
    
    # Add birth decade distribution
    report += f"""
### Artist Birth Decade Distribution
| Decade | Count | Percentage |
|--------|-------|------------|
"""
    
    for entry in artist_analysis.get("Birth decade distribution", []):
        report += f"| {entry['decade']} | {entry['count']} | {entry['percentage']:.2f}% |\n"
    
    # Add label analysis
    report += f"""
## Label Analysis
| Metric | Value |
|--------|-------|
"""
    
    for metric, value in label_analysis.items():
        if metric != "Top labels":
            if isinstance(value, float):
                report += f"| {metric} | {value:.2f}% |\n"
            else:
                report += f"| {metric} | {value} |\n"
    
    # Add top labels
    report += f"""
### Top Record Labels
| Label | Tracks | Percentage |
|-------|--------|------------|
"""
    
    for entry in label_analysis.get("Top labels", []):
        report += f"| {entry['label']} | {entry['tracks']} | {entry['percentage']:.2f}% |\n"
    
    # Add ontology utilization metrics
    report += f"""
## Ontology Utilization
| Metric | Value |
|--------|-------|
| Time ontology entities | {time_entities_total} |
| Time ontology relationships | {time_rels_total} |
"""
    
    # Save the report to a file
    report_path = os.path.join(output_dir, "knowledge_graph_analysis.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Comprehensive analysis report saved to {report_path}")

def main():
    # Load the generated knowledge graph
    print(f"Loading knowledge graph from {OUTPUT_PATH}...")
    graph = load_graph(OUTPUT_PATH)
    
    # Count total triples
    total_triples = len(graph)
    print(f"Total triples in the knowledge graph: {total_triples}")
    
    # Count entity types
    print("Counting entity types...")
    entity_counts = count_entity_types(graph)
    
    # Count relationship types
    print("Counting relationship types...")
    relationship_counts = count_relationship_types(graph)
    
    # Analyze time relationships
    print("Analyzing time relationships...")
    time_analysis = analyze_time_relationships(graph)
    
    # Calculate time ontology utilization
    time_entities_total = entity_counts.get('Time Instants', 0) + entity_counts.get('Time Intervals', 0) + entity_counts.get('Time Durations', 0)
    time_rels_total = sum([count for rel_type, count in relationship_counts.items() if rel_type.startswith('time:') or 'instant' in rel_type or 'interval' in rel_type or 'duration' in rel_type])
    
    # Analyze lyrics
    print("Analyzing lyrics...")
    lyrics_analysis = analyze_lyrics(graph)
    
    # Analyze additional roles
    print("Analyzing additional roles...")
    roles_analysis = analyze_additional_roles(graph)
    
    # Analyze artist data
    print("Analyzing artist data...")
    artist_analysis = analyze_artists(graph)
    
    # Analyze label data
    print("Analyzing label data...")
    label_analysis = analyze_labels(graph)
    
    # Analyze chart runs
    print("Analyzing chart runs...")
    chart_runs_analysis = analyze_chart_runs(graph)
    
    # Print summary
    print("\nSummary:")
    print(f"- Total triples: {total_triples}")
    print(f"- Total entities: {sum(entity_counts.values())}")
    print(f"- Total relationships: {sum(relationship_counts.values())}")
    print(f"- Most common entity: {max(entity_counts.items(), key=lambda x: x[1])}")
    print(f"- Most common relationship: {max(relationship_counts.items(), key=lambda x: x[1])}")
    
    # Create output directory
    output_dir = os.path.dirname(OUTPUT_PATH)
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate comprehensive report
    generate_comprehensive_report(
        output_dir, 
        total_triples, 
        entity_counts, 
        relationship_counts,
        time_analysis, 
        lyrics_analysis, 
        roles_analysis,
        artist_analysis,
        label_analysis,
        chart_runs_analysis,
        time_entities_total, 
        time_rels_total
    )
    
    print("\nAnalysis completed successfully!")

if __name__ == "__main__":
    main() 