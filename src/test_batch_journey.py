from rdflib import Graph
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]
QUERY = BASE_DIR / config["paths"]["sparql_batch_journey"]
g = Graph()
g.parse(ONTOLOGY)

with open(QUERY, "r", encoding="utf-8") as f:
    query = f.read()

results = list(g.query(query))

print("Journey events:", len(results))

for row in results:
    actor = str(row.actor).split("#")[-1] if row.actor else "-"

    print(
        row.eventID,
        "|", row.eventType,
        "|", row.timestamp,
        "|", actor,
        "| block", row.blockNumber,
        "| txHash", row.txHash
    )

if len(results) == 25:
    print("\nPASS: DL001 end-to-end journey contains 25 events.")
else:
    print("\nCHECK: Expected 25 events, got", len(results))