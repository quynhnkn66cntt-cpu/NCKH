from rdflib import Graph, Namespace
from pathlib import Path
import yaml
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

if len(sys.argv) != 2:
    print("Usage: python trace_distribution.py DL001")
    sys.exit(1)

distribution_id = sys.argv[1].strip().upper()

g = Graph()
g.parse(ONTOLOGY)

distribution_lot = NS[f"DistributionLot_{distribution_id}"]

# Kiểm tra mã có tồn tại
if not any(g.triples((distribution_lot, None, None))):
    print(f"ERROR: Distribution lot {distribution_id} not found.")
    sys.exit(1)

query = """
PREFIX : <http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#>

SELECT DISTINCT
    ?eventID
    ?eventType
    ?timestamp
    ?actor
    ?txHash
    ?blockNumber
WHERE {

    VALUES ?distributionLot {
        <%s>
    }

    ?distributionLot :distributedFrom ?shipment .
    ?shipment :shipsLot ?processingLot .
    ?processingLot :processedFrom ?harvestLot .
    ?harvestLot :harvestedFrom ?pond .

    {
        ?event :occursAtPond ?pond .
    }
    UNION
    {
        ?processingLot :hasEvent ?event .
    }
    UNION
    {
        ?shipment :hasEvent ?event .
    }
    UNION
    {
        ?distributionLot :hasEvent ?event .
    }

    ?event :eventID ?eventID ;
           :eventType ?eventType ;
           :timestamp ?timestamp ;
           :txHash ?txHash ;
           :blockNumber ?blockNumber .

    OPTIONAL {
        ?event :performedBy ?actor .
    }
}
ORDER BY ?timestamp ?eventID
""" % distribution_lot

results = list(g.query(query))

print("=" * 70)
print("TRACEABILITY JOURNEY:", distribution_id)
print("TOTAL EVENTS:", len(results))
print("=" * 70)

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