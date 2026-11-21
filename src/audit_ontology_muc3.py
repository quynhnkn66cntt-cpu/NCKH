
from pathlib import Path
from collections import Counter
from rdflib import Graph, RDF, OWL, URIRef
from rdflib.namespace import RDFS
from pyshacl import validate

ROOT = Path(__file__).resolve().parent.parent

OWL_FILE = ROOT / "03_ontology/owl/ontology_3_blockchain_enriched_new_namespace.owl"
SHACL_FILE = ROOT / "03_ontology/shacl/traceability_shapes.ttl"

NS = "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"

g = Graph()
g.parse(OWL_FILE, format="xml")

def uri(name):
    return URIRef(NS + name)

individuals = set(g.subjects(RDF.type, OWL.NamedIndividual))
classes = set(g.subjects(RDF.type, OWL.Class))
object_properties = set(g.subjects(RDF.type, OWL.ObjectProperty))

events = set(g.subjects(RDF.type, uri("TraceabilityEvent")))

print("========== ONTOLOGY AUDIT ==========")
print("Triples:", len(g))
print("Classes:", len(classes))
print("Object properties:", len(object_properties))
print("Named individuals:", len(individuals))
print("Traceability events:", len(events))

# Kiểm tra các thuộc tính bắt buộc
required = [
    "eventID",
    "timestamp",
    "performedBy",
    "batchID",
    "dataHash",
    "currentHash",
    "txHash",
    "blockNumber",
]

errors = []

for event in sorted(events, key=str):
    for name in required:
        values = list(g.objects(event, uri(name)))
        if len(values) != 1:
            errors.append(
                f"{event.split('#')[-1]}: {name} has {len(values)} values"
            )

# Kiểm tra eventID trùng lặp
ids = [
    str(value)
    for event in events
    for value in g.objects(event, uri("eventID"))
]

for event_id, count in Counter(ids).items():
    if count > 1:
        errors.append(f"Duplicate eventID: {event_id}")

# Kiểm tra đích của Object Properties
# Chỉ kiểm tra các liên kết giữa cá thể dữ liệu,
# không kiểm tra các định nghĩa OWL/SWRL.
for subject, predicate, target in g:
    if (
        subject in individuals
        and predicate in object_properties
        and isinstance(target, URIRef)
        and target not in individuals
    ):
        errors.append(
            f"Unresolved individual: "
            f"{subject.split('#')[-1]} -> "
            f"{predicate.split('#')[-1]} -> "
            f"{target.split('#')[-1]}"
        )

print("\n========== STRUCTURAL ISSUES ==========")
print("Total issues:", len(errors))

for error in errors[:50]:
    print("-", error)

if len(errors) > 50:
    print("Additional issues:", len(errors) - 50)

# Kiểm tra SHACL
shapes = Graph()
shapes.parse(SHACL_FILE, format="turtle")

conforms, _, report = validate(
    data_graph=g,
    shacl_graph=shapes,
    inference="rdfs",
    abort_on_first=False,
    advanced=True,
)

print("\n========== SHACL ==========")
print("Conforms:", conforms)

if not conforms:
    print(report)

print("\n========== RESULT ==========")

if not errors and conforms and len(events) > 0:
    print("PASS: Structural checks and SHACL passed.")
else:
    print("REVIEW: Ontology needs further inspection.")