from rdflib import Graph, RDF, Namespace
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]

SWRL = Namespace("http://www.w3.org/2003/11/swrl#")
g = Graph()
g.parse(ONTOLOGY)

variables = sorted(
    set(g.subjects(RDF.type, SWRL.Variable)),
    key=lambda x: str(x)
)

print("=" * 70)
print("SWRL VARIABLES")
print("=" * 70)
print("Total variables:", len(variables))

for v in variables:
    print(v)

print("\nCHECK IMPORTANT VARIABLES")

for name in ["pond", "harvest", "processing"]:
    matches = [v for v in variables if str(v).endswith("/" + name)
               or str(v).endswith("#" + name)]
    print(f"{name}: {matches if matches else 'NOT DECLARED'}")