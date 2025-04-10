import rdflib
from rdflib import Namespace, URIRef, Literal, Graph
import re
import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import OpenAI

load_dotenv()
open_api_key = os.environ.get("OPENAI_API_KEY")

print("Initializing OpenAI LLM...")
llm = OpenAI(
    model_name="gpt-4o-mini",
    temperature=0.1,
    openai_api_key=open_api_key,
)

# Replace with your local configuration as needed.
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# Define namespaces as declared in your TTL files.
MO = Namespace("http://example.org/mo#")
EX = Namespace("http://example.org/billboard#")
TIME = Namespace("http://example.org/time#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

# Paths to your files
graph_path = "output/music_knowledge_graph.ttl"
mo_ontology = "ontologies/music_ontology.ttl"
bb_ontology = "ontologies/billboard.ttl"
time_ontology = "ontologies/time.ttl"

# Create a single RDF graph and load ontologies and main graph.
g = Graph()
print("Parsing ontologies and main graph...")
g.parse(mo_ontology, format="turtle")
g.parse(bb_ontology, format="turtle")
g.parse(time_ontology, format="turtle")
g.parse(graph_path, format="turtle")
print(f"Graph loaded with {len(g)} triples.")
q = """
PREFIX mo: <http://example.org/mo#>
SELECT (COUNT(?s) AS ?total) WHERE {
  ?s mo:hasGender mo:gender_unknown .
}
"""
for row in g.query(q):
    print("Total with unknown gender:", row.total)


def load_graph(turtle_file):
    print(f"Loading graph from: {turtle_file}")
    graph = rdflib.Graph()
    graph.parse(turtle_file, format='turtle')
    return graph

def query_artists_with_unknown_gender(graph):
    print("Querying artists with unknown gender...")
    query = """
    PREFIX mo: <http://example.org/mo#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?artistName ?legalName ?dob (SAMPLE(?songTitle) AS ?oneSong) WHERE {
        ?artist a mo:MusicArtist ;
                mo:hasGender mo:gender_unknown ;
                rdfs:label ?artistName ;
                mo:legalName ?legalName ;
                mo:dateOfBirth ?dob ;
                mo:hasTrack ?track .
        ?track rdfs:label ?songTitle .
    }
    GROUP BY ?artistName ?legalName ?dob
    ORDER BY ?artistName
    """
    results = graph.query(query)
    print(f"Found {len(results)} artists with unknown gender.")
    unknown_gender_artists = []
    for row in results:
        unknown_gender_artists.append({
            "artist_uri": None,
            "artist_label": str(row.artistName),
            "legalName": str(row.legalName) if row.legalName else None,
            "dateOfBirth": str(row.dob) if row.dob else None,
            "sampleSong": str(row.oneSong) if row.oneSong else None
        })
    return unknown_gender_artists

def wikidata_artist_query(artist_info):
    artist_label = artist_info["artist_label"]
    print(f"Querying Wikidata for: {artist_label}")
    query = f"""
    SELECT ?artist ?artistLabel ?birthName ?dob ?genderLabel ?songLabel WHERE {{
      ?artist rdfs:label "{artist_label}"@en.
      ?artist wdt:P31 wd:Q5 .
      ?artist wdt:P106 wd:Q639669 .
      OPTIONAL {{ ?artist wdt:P1477 ?birthName. }}
      OPTIONAL {{ ?artist wdt:P569 ?dob. }}
      OPTIONAL {{ ?artist wdt:P21 ?gender. }}
      OPTIONAL {{
          ?song wdt:P175 ?artist.
          ?song rdfs:label ?songLabel.
          FILTER(LANG(?songLabel) = "en")
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """
    headers = {'Accept': 'application/sparql-results+json'}
    try:
        response = requests.get(WIKIDATA_ENDPOINT, params={'query': query}, headers=headers)
        data = response.json()
        results = data['results']['bindings']
        if results:
            result = results[0]
            print("Wikidata info retrieved.")
            return {
                "artist": artist_label,
                "legalName": result.get("birthName", {}).get("value", None),
                "dateOfBirth": result.get("dob", {}).get("value", None),
                "retrievedGender": result.get("genderLabel", {}).get("value", "").lower() or "unknown",
                "sampleSong": result.get("songLabel", {}).get("value", None)
            }
        else:
            print("No Wikidata match found.")
            return None
    except Exception as e:
        print(f"Error querying Wikidata for '{artist_label}': {e}")
        return None

prompt_template = PromptTemplate(
    input_variables=["artist", "retrievedGender", "artist_slug"],
    template="""
You are an RDF triple generator. Given the following data for an artist:
- Artist: {artist}
- Retrieved gender from Wikidata: {retrievedGender}

Mapping rules:
- If the retrieved gender is "male", generate the triple:
  <http://example.org/artist/{artist_slug}> mo:hasGender <http://example.org/mo#gender_male> .
- If it is "female", generate the triple:
  <http://example.org/artist/{artist_slug}> mo:hasGender <http://example.org/mo#gender_female> .
- Otherwise, generate the triple:
  <http://example.org/artist/{artist_slug}> mo:hasGender <http://example.org/mo#gender_unknown> .

Output exactly one RDF triple in Turtle syntax.
""",
)
chain = LLMChain(llm=llm, prompt=prompt_template)

def artist_to_slug(artist_name):
    slug = re.sub(r'\s+', '-', artist_name.strip().lower())
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    return slug

def generate_gender_triple(artist_info):
    artist_name = artist_info.get("artist")
    retrieved_gender = artist_info.get("retrievedGender") or "unknown"
    slug = artist_to_slug(artist_name)
    prompt_inputs = {
        "artist": artist_name,
        "retrievedGender": retrieved_gender,
        "artist_slug": slug
    }
    print(f"Generating RDF triple for {artist_name} with gender '{retrieved_gender}'...")
    triple = chain.run(prompt_inputs)
    print(f"Generated triple: {triple.strip()}")
    return triple.strip()

def update_missing_artist_info(turtle_file):
    graph = load_graph(turtle_file)
    missing_artists = query_artists_with_unknown_gender(graph)

    final_updates = []
    for artist in missing_artists:
        print("=" * 40)
        print(f"Processing: {artist['artist_label']}")
        wikidata_info = wikidata_artist_query(artist)
        if wikidata_info:
            rdf_triple = generate_gender_triple(wikidata_info)
            final_updates.append({
                "artist": artist["artist_label"],
                "artist_uri": artist["artist_uri"],
                "legalName": wikidata_info.get("legalName"),
                "dateOfBirth": wikidata_info.get("dateOfBirth"),
                "retrievedGender": wikidata_info.get("retrievedGender"),
                "sampleSong": wikidata_info.get("sampleSong"),
                "rdfTriple": rdf_triple
            })
        else:
            print(f"No Wikidata info found for: {artist['artist_label']}")
    
    df_updates = pd.DataFrame(final_updates)
    df_updates.to_csv("artists_gender_updates.csv", index=False, encoding="utf-8")
    print("Saved CSV output: artists_gender_updates.csv")

    with open("artists_gender_updates.json", "w", encoding="utf-8") as f:
        json.dump(final_updates, f, indent=2)
    print("Saved JSON output: artists_gender_updates.json")

    ttl_graph = rdflib.Graph()
    ttl_graph.bind("mo", MO)
    for update in final_updates:
        try:
            ttl_graph.parse(data=update["rdfTriple"], format="turtle")
        except Exception as e:
            print(f"Error parsing triple for {update['artist']}: {e}")
    ttl_graph.serialize("artists_gender_updates.ttl", format="turtle")
    print("Saved Turtle output: artists_gender_updates.ttl")

    return final_updates

if __name__ == "__main__":
    updates = update_missing_artist_info(graph_path)
