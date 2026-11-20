from rdflib import Graph, RDF, OWL, RDFS, Namespace
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

g = Graph()
g.parse(ONTOLOGY)

classes = set(g.subjects(RDF.type, OWL.Class))
object_properties = set(g.subjects(RDF.type, OWL.ObjectProperty))
datatype_properties = set(g.subjects(RDF.type, OWL.DatatypeProperty))
named_individuals = set(g.subjects(RDF.type, OWL.NamedIndividual))

# TraceabilityEvent và các cá thể thuộc lớp con của TraceabilityEvent
event_classes = {NS.TraceabilityEvent}

for cls in g.subjects(RDFS.subClassOf, NS.TraceabilityEvent):
    event_classes.add(cls)

traceability_events = set()

for cls in event_classes:
    traceability_events.update(g.subjects(RDF.type, cls))

print("========================================")
print("ONTOLOGY STATISTICS")
print("========================================")
print("Total triples          :", len(g))
print("OWL classes            :", len(classes))
print("Object properties      :", len(object_properties))
print("Datatype properties    :", len(datatype_properties))
print("Named individuals      :", len(named_individuals))
print("TraceabilityEvent      :", len(traceability_events))

print("\n========================================")
print("EVENT TYPE STATISTICS")
print("========================================")

event_types = [
    "StockingEvent",
    "FeedingEvent",
    "TreatmentEvent",
    "HarvestEvent",
    "ProcessingEvent",
    "ShipmentEvent",
    "DistributionEvent"
]

total_event_types = 0

for name in event_types:
    cls = NS[name]
    count = len(set(g.subjects(RDF.type, cls)))
    total_event_types += count
    print(f"{name:<20}: {count}")

print("----------------------------------------")
print("Total typed events     :", total_event_types)