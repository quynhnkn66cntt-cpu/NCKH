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

pond = NS.Pond_P001

events = list(g.subjects(NS.occursAtPond, pond))

print("Ontology:", ONTOLOGY)
print("Events at P001:", len(events))

rows = []

for event in events:
    event_id = g.value(event, NS.eventID)
    event_type = g.value(event, NS.eventType)
    timestamp = g.value(event, NS.timestamp)
    block_number = g.value(event, NS.blockNumber)

    rows.append(
        (
            str(event_id),
            str(event_type),
            str(timestamp),
            str(block_number)
        )
    )

rows.sort(key=lambda x: (x[2], x[0]))

for event_id, event_type, timestamp, block in rows:
    print(
        event_id,
        "|", event_type,
        "|", timestamp,
        "| block", block
    )