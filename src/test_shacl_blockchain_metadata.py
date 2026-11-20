from pathlib import Path
import yaml

from rdflib import Graph, Namespace
from pyshacl import validate

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]
SHAPES = BASE_DIR / config["paths"]["shacl_shapes"]
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

data_graph = Graph()
data_graph.parse(ONTOLOGY)

shacl_graph = Graph()
shacl_graph.parse(SHAPES, format="turtle")

ev001 = NS.TraceabilityEvent_EV001

# Chỉ xóa trong bộ nhớ.
# File ontology thật KHÔNG bị thay đổi.
data_graph.remove((ev001, NS.txHash, None))
data_graph.remove((ev001, NS.blockNumber, None))

conforms, results_graph, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shacl_graph,
    inference="rdfs",
    abort_on_first=False,
    allow_infos=False,
    allow_warnings=False
)

print("=" * 60)
print("NEGATIVE TEST: REMOVE BLOCKCHAIN METADATA FROM EV001")
print("=" * 60)
print("Conforms:", conforms)
print()
print(results_text)

if conforms:
    print("FAIL: SHACL did not detect missing blockchain metadata.")
else:
    print("PASS: SHACL detected missing txHash/blockNumber.")