from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

INPUT = BASE_DIR / config["paths"]["ontology_output"]

OUTPUT = BASE_DIR / config["paths"]["ontology_blockchain"]
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

g = Graph()
g.parse(INPUT)

block_number = NS.blockNumber

g.add((block_number, RDF.type, OWL.DatatypeProperty))
g.add((block_number, RDFS.domain, NS.TraceabilityEvent))
g.add((block_number, RDFS.range, XSD.long))

g.serialize(OUTPUT, format="xml")

print("Output:", OUTPUT)
print("Triples:", len(g))
print(
    "blockNumber declared:",
    (block_number, RDF.type, OWL.DatatypeProperty) in g
)