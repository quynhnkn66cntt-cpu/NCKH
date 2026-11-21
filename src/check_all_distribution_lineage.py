from pathlib import Path
import yaml
from rdflib import Graph, Namespace

# ============================================================
# LOAD CONFIG
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]

NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

# ============================================================
# LOAD ONTOLOGY
# ============================================================

g = Graph()
g.parse(ONTOLOGY)

# ============================================================
# CHECK DISTRIBUTION LINEAGE
# ============================================================

for i in range(1, 6):
    dl_id = f"DL{i:03d}"
    dl = NS[f"DistributionLot_{dl_id}"]

    shipment = g.value(dl, NS.distributedFrom)
    processing = g.value(shipment, NS.shipsLot) if shipment else None
    harvest = g.value(processing, NS.processedFrom) if processing else None
    pond = g.value(harvest, NS.harvestedFrom) if harvest else None

    def name(uri):
        return str(uri).split("#")[-1] if uri else "MISSING"

    print(
        dl_id,
        "->", name(shipment),
        "->", name(processing),
        "->", name(harvest),
        "->", name(pond)
    )