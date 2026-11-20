import json
import hashlib
import re

from flask import jsonify
from fabric_client import get_blockchain_event
from pathlib import Path
import yaml
from flask import Flask, request, render_template
from rdflib import Graph, Namespace

# ============================================================
# LOAD CONFIG
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]

app = Flask(__name__)
NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/2026/6/shrimp-traceability#"
)

g = Graph()
g.parse(ONTOLOGY)


def trace_distribution(distribution_id):

    distribution_id = distribution_id.strip().upper()
    distribution_lot = NS[f"DistributionLot_{distribution_id}"]

    # Kiểm tra lô có tồn tại
    if not any(g.triples((distribution_lot, None, None))):
        return None

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

    results = []

    for row in g.query(query):
        results.append({
            "eventID": str(row.eventID),
            "eventType": str(row.eventType),
            "timestamp": str(row.timestamp),
            "actor": (
                str(row.actor).split("#")[-1]
                if row.actor else "-"
            ),
            "blockNumber": str(row.blockNumber),
            "txHash": str(row.txHash)
        })
    return results


@app.route("/")
def home():
    lot_id = request.args.get("lot", "").strip().upper()
    events = None

    if lot_id:
        events = trace_distribution(lot_id)

    return render_template(
        "index.html",
        lot_id=lot_id,
        events=events
    )

# ============================================================
# VERIFY INTEGRITY
# ============================================================

EVENT_DIR = BASE_DIR / "02_preprocessed/mapped/hashed_events"


@app.route("/verify/<event_id>")
def verify_integrity(event_id):

    event_id = event_id.strip().upper()

    # Chỉ cho phép mã sự kiện hợp lệ
    if not re.fullmatch(r"EV\d+", event_id):
        return jsonify({
            "status": "UNVERIFIED",
            "message": "Invalid event ID"
        }), 400

    event_file = EVENT_DIR / f"{event_id}.json"

    if not event_file.is_file():
        return jsonify({
            "status": "UNVERIFIED",
            "message": "Off-chain event not found"
        }), 404

    try:
        # 1. Đọc dữ liệu off-chain
        with open(event_file, encoding="utf-8") as f:
            event = json.load(f)

        # 2. Tính lại SHA-256
        data_string = json.dumps(
            event["data"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":")
        )

        calculated_hash = hashlib.sha256(
            data_string.encode("utf-8")
        ).hexdigest()

        # 3. Đọc hash trực tiếp từ Blockchain
        blockchain_event = get_blockchain_event(event_id)

        if blockchain_event.get("eventID") != event_id:
            return jsonify({
                "status": "UNVERIFIED",
                "message": "Blockchain event ID mismatch"
            }), 503

        blockchain_hash = blockchain_event["dataHash"]

        # 4. So sánh
        if calculated_hash == blockchain_hash:
            status = "VALID"
        else:
            status = "TAMPERED"

        return jsonify({
            "eventID": event_id,
            "status": status,
            "calculatedHash": calculated_hash,
            "blockchainHash": blockchain_hash,
            "txId": blockchain_event.get("txId")
        })

    except (OSError, ValueError, KeyError, TypeError) as e:
        app.logger.warning("Verification data error: %s", e)
        return jsonify({
            "status": "UNVERIFIED",
            "message": "Verification data unavailable"
        }), 503

    except Exception as e:
        app.logger.warning("Blockchain verification error: %s", e)
        return jsonify({
            "status": "UNVERIFIED",
            "message": "Blockchain verification unavailable"
        }), 503
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
