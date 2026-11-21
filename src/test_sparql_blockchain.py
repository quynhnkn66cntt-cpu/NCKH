
from rdflib import Graph, Namespace
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]
QUERY = BASE_DIR / config["paths"]["sparql_blockchain_metadata"]

g = Graph()
g.parse(ONTOLOGY)

# Đếm số sự kiện từ dữ liệu Ontology, không cố định 116.
expected_count = len(set(g.subjects(NS.eventID, None)))

query = QUERY.read_text(encoding="utf-8")
results = list(g.query(query))

# Kiểm tra tính đầy đủ và duy nhất của kết quả.
result_ids = [str(row.eventID) for row in results]
unique_ids = set(result_ids)

metadata_complete = all(
    row.txHash is not None
    and str(row.txHash).strip() != ""
    and row.blockNumber is not None
    for row in results
)

print("=" * 50)
print("SPARQL BLOCKCHAIN METADATA TEST")
print("=" * 50)
print("Expected events :", expected_count)
print("Query results   :", len(results))
print("Unique eventIDs :", len(unique_ids))
print("Metadata complete:", metadata_complete)

for row in results[:3]:
    print(
        row.eventID,
        "| txHash =", row.txHash,
        "| block =", row.blockNumber
    )

print("...")

for row in results[-3:]:
    print(
        row.eventID,
        "| txHash =", row.txHash,
        "| block =", row.blockNumber
    )

if (
    expected_count > 0
    and len(results) == expected_count
    and len(unique_ids) == expected_count
    and metadata_complete
):
    print("PASS: All events have unique IDs and blockchain metadata.")
else:
    print("FAIL: Event count, uniqueness, or metadata validation failed.")
