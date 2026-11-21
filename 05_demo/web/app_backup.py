from pathlib import Path
import yaml
from flask import Flask, request
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
    "http://www.semanticweb.org/pc/ontologies/2026/6/untitled-ontology-12#"
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
    PREFIX : <http://www.semanticweb.org/pc/ontologies/2026/6/untitled-ontology-12#>

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

    html = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Truy xuất nguồn gốc tôm nuôi</title>
    </head>
    <body>

    <h1>HỆ THỐNG TRUY XUẤT NGUỒN GỐC TÔM NUÔI</h1>

    <p>Blockchain kết hợp Ontology</p>

    <form method="get">
        <label>Mã lô phân phối:</label>
        <input
            type="text"
            name="lot"
            placeholder="Ví dụ: DL001"
            value="%s"
        >
        <button type="submit">Truy xuất</button>
    </form>
    """ % lot_id

    if lot_id and events is None:
        html += "<h3>Không tìm thấy mã lô %s</h3>" % lot_id

    elif events is not None:

        html += "<h2>Kết quả truy xuất: %s</h2>" % lot_id
        html += "<p>Tổng số sự kiện: %d</p>" % len(events)

        html += """
        <table border="1" cellpadding="7">
            <tr>
                <th>Event</th>
                <th>Loại sự kiện</th>
                <th>Thời gian</th>
                <th>Actor</th>
                <th>Block</th>
                <th>TxHash</th>
            </tr>
        """

        for event in events:
            html += """
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>
            """ % (
                event["eventID"],
                event["eventType"],
                event["timestamp"],
                event["actor"],
                event["blockNumber"],
                event["txHash"]
            )

        html += "</table>"

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)