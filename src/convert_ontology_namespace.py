
from pathlib import Path
from rdflib import Graph, URIRef

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT = PROJECT_DIR / "03_ontology/owl/ontology_backup_before_merge.owl"
OUTPUT = PROJECT_DIR / "03_ontology/owl/ontology_base_new_namespace.owl"

OLD_BASE = "http://www.semanticweb.org/pc/ontologies/2026/6/untitled-ontology-12"
NEW_BASE = "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability"

g = Graph()
g.parse(INPUT, format="xml")

new_g = Graph()

for prefix, namespace in g.namespaces():
    new_g.bind(prefix, namespace)

def convert_uri(value):
    if isinstance(value, URIRef):
        uri = str(value)

        if uri == OLD_BASE or uri.startswith(OLD_BASE + "#"):
            return URIRef(NEW_BASE + uri[len(OLD_BASE):])

    return value

for s, p, o in g:
    new_g.add((
        convert_uri(s),
        convert_uri(p),
        convert_uri(o)
    ))

# Kiểm tra không làm mất RDF triples
assert len(g) == len(new_g), "So luong triples thay doi!"

# Không ghi đè file đã tồn tại
if OUTPUT.exists():
    raise FileExistsError(f"File da ton tai: {OUTPUT}")

new_g.serialize(destination=OUTPUT, format="xml")

print("Chuyen namespace thanh cong")
print("Triples ban dau:", len(g))
print("Triples sau chuyen:", len(new_g))
print("Output:", OUTPUT)
