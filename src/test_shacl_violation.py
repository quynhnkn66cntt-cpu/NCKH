from pathlib import Path
import yaml

from rdflib import Graph, Namespace
from pyshacl import validate

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

DATA_FILE = BASE_DIR / config["paths"]["ontology_blockchain"]
SHAPES_FILE = BASE_DIR / config["paths"]["shacl_shapes"]
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

# Đọc ontology hoàn chỉnh
data_graph = Graph()
data_graph.parse(DATA_FILE)

# Cố ý tạo lỗi:
# xóa currentHash của EV001 trong bộ nhớ
# KHÔNG làm thay đổi file ontology thật.
event = NS.TraceabilityEvent_EV001
data_graph.remove((event, NS.currentHash, None))

print("TEST: Removed currentHash from TraceabilityEvent_EV001")

# Chạy SHACL
conforms, results_graph, results_text = validate(
    data_graph=data_graph,
    shacl_graph=str(SHAPES_FILE),
    shacl_graph_format="turtle",
    inference="rdfs",
    abort_on_first=False,
)

print("\n" + "=" * 60)
print("SHACL NEGATIVE TEST")
print("=" * 60)

print("Conforms:", conforms)
print(results_text)