import os
import sys

src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

from rdflib import Graph, Namespace, RDF
from config import NAMESPACES, OUTPUT_PATH

def count_entities():
    # Load the graph
    g = Graph()
    g.parse(OUTPUT_PATH, format="turtle")
    
    # Create namespace objects
    mo = Namespace(NAMESPACES['mo'])
    ex = Namespace(NAMESPACES['ex'])
    time = Namespace(NAMESPACES['time'])
    
    # Count entities by type
    print(f"Total triples: {len(g)}")
    print("\nCounts by entity type:")
    print(f"Tracks: {len(list(g.subjects(RDF.type, mo.Track)))}")
    print(f"Music Artists: {len(list(g.subjects(RDF.type, mo.MusicArtist)))}")
    print(f"Music Writers: {len(list(g.subjects(RDF.type, mo.MusicWriter)))}")
    print(f"Music Producers: {len(list(g.subjects(RDF.type, Namespace('http://example.org/mo#').MusicProducer)))}")
    print(f"Languages: {len(list(g.subjects(RDF.type, mo.Language)))}")
    print(f"Genders: {len(list(g.subjects(RDF.type, mo.Gender)))}")
    print(f"Chart Entries: {len(list(g.subjects(RDF.type, ex.ChartEntry)))}")
    print(f"Music Charts: {len(list(g.subjects(RDF.type, ex.MusicChart)))}")
    print(f"Time Instants: {len(list(g.subjects(RDF.type, time.Instant)))}")
    
    # Count relationships
    print("\nCounts by relationship type:")
    print(f"track-artist links: {len(list(g.triples((None, mo.hasMusicArtist, None))))}")
    print(f"track-writer links: {len(list(g.triples((None, mo.hasWriter, None))))}")
    print(f"track-producer links: {len(list(g.triples((None, mo.hasProducer, None))))}")
    print(f"track-language links: {len(list(g.triples((None, mo.hasLanguage, None))))}")
    print(f"artist-gender links: {len(list(g.triples((None, mo.hasGender, None))))}")
    print(f"artist-legal name links: {len(list(g.triples((None, mo.hasLegalName, None))))}")
    print(f"chart entry-position links: {len(list(g.triples((None, ex.chartPosition, None))))}")
    print(f"chart entry-track links: {len(list(g.triples((None, mo.forTrack, None))))}")

if __name__ == "__main__":
    count_entities() 