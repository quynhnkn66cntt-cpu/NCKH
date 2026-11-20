import csv
from pathlib import Path
import yaml

from rdflib import Graph, Namespace, Literal
from rdflib.namespace import XSD

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]
METADATA = BASE_DIR / config["paths"]["blockchain_metadata"]
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

g = Graph()
g.parse(ONTOLOGY)

with open(METADATA, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

updated = 0
missing_events = []

for row in rows:
    event_id = row["eventID"]
    tx_id = row["txId"]
    block_number = row["blockNumber"]

    event_uri = NS[f"TraceabilityEvent_{event_id}"]

    # Đảm bảo individual thật sự tồn tại trong ontology
    if not list(g.predicate_objects(event_uri)):
        missing_events.append(event_id)
        continue

    # Tránh tạo giá trị trùng nếu script được chạy lại
    g.remove((event_uri, NS.txHash, None))
    g.remove((event_uri, NS.blockNumber, None))

    g.add((
        event_uri,
        NS.txHash,
        Literal(tx_id, datatype=XSD.string)
    ))

    g.add((
        event_uri,
        NS.blockNumber,
        Literal(int(block_number), datatype=XSD.long)
    ))

    updated += 1

g.serialize(ONTOLOGY, format="xml")

print("Metadata rows:", len(rows))
print("Events updated:", updated)
print("Missing events:", missing_events)
print("Triples:", len(g))
print("Saved:", ONTOLOGY)