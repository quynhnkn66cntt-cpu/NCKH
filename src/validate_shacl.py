from rdflib import Graph
from pyshacl import validate
from pathlib import Path
import yaml

# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

DATA_FILE = BASE_DIR / config["paths"]["ontology_blockchain"]
SHAPES_FILE = BASE_DIR / config["paths"]["shacl_shapes"]
# ============================================================
# LOAD ONTOLOGY
# ============================================================

data_graph = Graph()
data_graph.parse(DATA_FILE)

print("Ontology loaded.")
print("Ontology triples:", len(data_graph))

# ============================================================
# LOAD SHACL SHAPES
# ============================================================

shacl_graph = Graph()
shacl_graph.parse(SHAPES_FILE, format="turtle")

print("SHACL shapes loaded.")
print("SHACL triples:", len(shacl_graph))

# ============================================================
# SHACL VALIDATION
# ============================================================

conforms, results_graph, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shacl_graph,
    inference="rdfs",
    abort_on_first=False,
    allow_infos=False,
    allow_warnings=False,
)

# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 60)
print("SHACL VALIDATION RESULT")
print("=" * 60)

print("Conforms:", conforms)

if conforms:
    print("PASS: Ontology conforms to all SHACL constraints.")
else:
    print("FAIL: Ontology contains SHACL constraint violations.")

print("\nDetailed report:")
print(results_text)