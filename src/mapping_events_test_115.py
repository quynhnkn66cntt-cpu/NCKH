import json
import re
from pathlib import Path
import yaml
import logging

from rdflib import Graph, Literal, Namespace, RDF, OWL
from rdflib.namespace import XSD

import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# =========================================================
# LOAD CONFIGURATION
# =========================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config_test_115.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

PROJECT_DIR = Path(config["project"]["root_dir"])

ONTOLOGY_INPUT = PROJECT_DIR / config["paths"]["ontology_input"]
ONTOLOGY_OUTPUT = PROJECT_DIR / config["paths"]["ontology_output"]
HASHED_EVENT_DIR = PROJECT_DIR / config["paths"]["hashed_events"]
PAYLOAD_DIR = PROJECT_DIR / config["paths"]["payloads"]
LOG_DIR = PROJECT_DIR / config["paths"]["logs"]


# =========================================================
# KIỂM TRA ĐƯỜNG DẪN
# =========================================================

print("Ontology exists:", ONTOLOGY_INPUT.exists())
print("JSON folder exists:", HASHED_EVENT_DIR.exists())
print(
    "JSON file count:",
    len(list(HASHED_EVENT_DIR.glob("EV*.json")))
)


LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "mapping_events.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

logger.info("Starting ontology event mapping...")


# =========================================================
# 2. NAMESPACE CỦA ONTOLOGY
# =========================================================

NS = Namespace(
    "http://www.semanticweb.org/pc/ontologies/"
    "2026/6/shrimp-traceability#"
)


# =========================================================
# 3. ÁNH XẠ LOẠI SỰ KIỆN → INDIVIDUAL NGHIỆP VỤ
# =========================================================

OWNER_PREFIX = {
    "SEED_STOCKING": "SeedLot_",
    "FEEDING": "FeedBatch_",
    "TREATMENT": "TreatmentRecord_",
    "HARVEST": "HarvestLot_",
    "PROCESSING": "ProcessingLot_",
    "SHIPPING": "Shipment_",
    "DISTRIBUTION": "DistributionLot_",
}


# =========================================================
# 3.1. ÁNH XẠ eventType → EVENT SUBCLASS
# =========================================================

EVENT_CLASS = {
    "SEED_STOCKING": NS.StockingEvent,
    "FEEDING": NS.FeedingEvent,
    "TREATMENT": NS.TreatmentEvent,
    "HARVEST": NS.HarvestEvent,
    "PROCESSING": NS.ProcessingEvent,
    "SHIPPING": NS.ShipmentEvent,
    "DISTRIBUTION": NS.DistributionEvent,
}


# =========================================================
# 3.2. CÁC LỚP ACTOR TRONG ONTOLOGY MỚI
# =========================================================

ACTOR_CLASSES = {
    NS.Actor,
    NS.Farm,
    NS.ProcessingPlant,
    NS.Transporter,
    NS.Distributor,
}


def event_number(path: Path) -> int:
    """
    Lấy số từ EV001.json để sắp xếp theo số EV.
    Thứ tự này dùng để đọc file/ledger,
    KHÔNG dùng để tạo hasPreviousEvent nghiệp vụ.
    """
    match = re.fullmatch(r"EV(\d+)\.json", path.name)

    if not match:
        raise ValueError(
            f"Tên file không hợp lệ: {path.name}"
        )

    return int(match.group(1))


# =========================================================
# 4. ĐỌC ONTOLOGY
# =========================================================

if not ONTOLOGY_INPUT.exists():
    raise FileNotFoundError(
        f"Không tìm thấy ontology: {ONTOLOGY_INPUT}"
    )

if not HASHED_EVENT_DIR.exists():
    raise FileNotFoundError(
        f"Không tìm thấy thư mục JSON: {HASHED_EVENT_DIR}"
    )

graph = Graph()
graph.parse(ONTOLOGY_INPUT, format="xml")

print("Ontology loaded.")
print("Initial triple count:", len(graph))


# =========================================================
# 5. XÓA CÁC TRACEABILITY EVENT MẪU CŨ
# =========================================================

old_events = list(
    graph.subjects(
        RDF.type,
        NS.TraceabilityEvent
    )
)

for event_uri in old_events:

    # Xóa các triple mà event là subject
    graph.remove((event_uri, None, None))

    # Xóa các liên kết trỏ tới event cũ
    graph.remove((None, None, event_uri))

print("Old events removed:", len(old_events))


# =========================================================
# 6. ĐỌC DANH SÁCH JSON
# =========================================================

event_files = sorted(
    HASHED_EVENT_DIR.glob("EV*.json"),
    key=event_number
)

expected_count = len(event_files)

if expected_count == 0:
    raise ValueError(
        "Không tìm thấy file sự kiện JSON để mapping."
    )

print("Số sự kiện đầu vào:", expected_count)


# =========================================================
# 7. MAPPING TRACEABILITY EVENT
# =========================================================

mapped_count = 0

for json_path in event_files:

    with json_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        event = json.load(file)

    expected_event_id = json_path.stem

    # -----------------------------------------------------
    # Kiểm tra ID
    # -----------------------------------------------------

    if event.get("eventID") != expected_event_id:
        raise ValueError(
            f"{json_path.name}: eventID không đúng. "
            f"Mong đợi {expected_event_id}, "
            f"nhận được {event.get('eventID')}"
        )

    # -----------------------------------------------------
    # Kiểm tra các trường bắt buộc
    # -----------------------------------------------------

    required_fields = [
        "eventID",
        "batchID",
        "eventType",
        "actorID",
        "timestamp",
        "dataHash",
        "previousEventHash",
        "currentHash",
        "data",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in event
    ]

    if missing_fields:
        raise ValueError(
            f"{expected_event_id} thiếu trường: "
            f"{missing_fields}"
        )

    event_id = event["eventID"]
    batch_id = event["batchID"]
    event_type = event["eventType"]
    actor_id = event["actorID"]

    event_uri = NS[
        f"TraceabilityEvent_{event_id}"
    ]

    actor_uri = NS[
        f"Actor_{actor_id}"
    ]

    # -----------------------------------------------------
    # Kiểm tra eventType
    # -----------------------------------------------------

    event_class = EVENT_CLASS.get(event_type)

    if event_class is None:
        raise ValueError(
            f"{event_id}: eventType chưa có Event subclass: "
            f"{event_type}"
        )

    # -----------------------------------------------------
    # Khai báo TraceabilityEvent
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Khai báo cá thể OWL
    # -----------------------------------------------------

    graph.add((
        event_uri,
        RDF.type,
        OWL.NamedIndividual
    ))

    # -----------------------------------------------------
    # Khai báo TraceabilityEvent
    # -----------------------------------------------------

    graph.add((
        event_uri,
        RDF.type,
        NS.TraceabilityEvent
    ))
    # -----------------------------------------------------
    # Gán EVENT SUBCLASS
    #
    # Ví dụ:
    # SEED_STOCKING → StockingEvent
    # SHIPPING      → ShipmentEvent
    # -----------------------------------------------------

    graph.add((
        event_uri,
        RDF.type,
        event_class
    ))

    # -----------------------------------------------------
    # Data properties
    # -----------------------------------------------------

    graph.add((
        event_uri,
        NS.eventID,
        Literal(
            event_id,
            datatype=XSD.string
        )
    ))

    graph.add((
        event_uri,
        NS.batchID,
        Literal(
            batch_id,
            datatype=XSD.string
        )
    ))

    # Giữ eventType để tương thích dữ liệu JSON
    # và hỗ trợ truy vấn/lọc dữ liệu khi cần.
    graph.add((
        event_uri,
        NS.eventType,
        Literal(
            event_type,
            datatype=XSD.string
        )
    ))

    graph.add((
        event_uri,
        NS.dataHash,
        Literal(
            event["dataHash"],
            datatype=XSD.string
        )
    ))

    graph.add((
    event_uri,
    NS.currentHash,
    Literal(
        event["currentHash"],
        datatype=XSD.string
    )
    ))
    graph.add((
        event_uri,
        NS.previousEventHash,
        Literal(
            event["previousEventHash"],
            datatype=XSD.string
        )
    ))

    graph.add((
        event_uri,
        NS.timestamp,
        Literal(
            event["timestamp"],
            datatype=XSD.dateTime
        )
    ))

    # documentURI dùng đường dẫn tương đối đến payload.
    # Sau này có URL thật thì cập nhật lại.
    document_uri = f"payloads/{event_id}.json"

    graph.add((
        event_uri,
        NS.documentURI,
        Literal(
            document_uri,
            datatype=XSD.string
        )
    ))

    # Chưa ghi blockchain thật.
    # Hiện tại dữ liệu hash đã được kiểm tra.
    graph.add((
        event_uri,
        NS.verificationStatus,
        Literal(
            "HASH_VERIFIED",
            datatype=XSD.string
        )
    ))

    # -----------------------------------------------------
    # Liên kết với tác nhân
    # -----------------------------------------------------

    actor_types = set(
        graph.objects(
            actor_uri,
            RDF.type
        )
    )

    valid_actor = bool(
        actor_types.intersection(
            ACTOR_CLASSES
        )
    )

    if not valid_actor:
        raise ValueError(
            f"{event_id}: không tìm thấy Actor_{actor_id} "
            f"thuộc Actor/Farm/ProcessingPlant/"
            f"Transporter/Distributor. "
            f"Types hiện có: "
            f"{[str(x) for x in actor_types]}"
        )

    graph.add((
        event_uri,
        NS.performedBy,
        actor_uri
    ))

    # -----------------------------------------------------
    # Liên kết với ao nuôi nếu JSON có pondID
    # -----------------------------------------------------

    event_data = event["data"]
    pond_id = event_data.get("pondID")

    if pond_id:

        pond_uri = NS[
            f"Pond_{pond_id}"
        ]

        if (
            pond_uri,
            RDF.type,
            NS.AoNuoi
        ) not in graph:
            raise ValueError(
                f"{event_id}: "
                f"không tìm thấy Pond_{pond_id}"
            )

        graph.add((
            event_uri,
            NS.occursAtPond,
            pond_uri
        ))

    # -----------------------------------------------------
    # Liên kết sự kiện với lô/bản ghi nghiệp vụ
    # -----------------------------------------------------

    owner_prefix = OWNER_PREFIX.get(event_type)

    if owner_prefix is None:
        raise ValueError(
            f"{event_id}: eventType chưa được hỗ trợ: "
            f"{event_type}"
        )

    owner_uri = NS[
        f"{owner_prefix}{batch_id}"
    ]

    # Kiểm tra individual nghiệp vụ đã tồn tại
    if not any(
        graph.triples(
            (owner_uri, None, None)
        )
    ):
        raise ValueError(
            f"{event_id}: không tìm thấy individual "
            f"{owner_prefix}{batch_id}"
        )

    graph.add((
        owner_uri,
        NS.hasEvent,
        event_uri
    ))

    mapped_count += 1


# =========================================================
# 8. XÂY DỰNG THỨ TỰ NGHIỆP VỤ CỦA SỰ KIỆN
#
# hasPreviousEvent:
#   - KHÔNG dựa trên số EV
#   - Dựa trên lineage của Pond
#   - Sắp xếp theo timestamp
#   - eventID chỉ dùng tie-break khi cùng timestamp
# =========================================================

business_events = []

for json_path in event_files:

    with json_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        event = json.load(file)

    business_events.append({
        "eventID": event["eventID"],
        "eventType": event["eventType"],
        "batchID": event["batchID"],
        "timestamp": event["timestamp"],
        "data": event["data"],
    })


# ---------------------------------------------------------
# Xác định lineage của các lô về ao nuôi
# ---------------------------------------------------------

harvest_to_pond = {}
processing_to_pond = {}
shipment_to_pond = {}
distribution_to_pond = {}


# ---------------------------------------------------------
# HarvestLot -> Pond
# ---------------------------------------------------------

for event in business_events:

    if event["eventType"] == "HARVEST":

        harvest_id = event["data"]["harvestLotID"]
        pond_id = event["data"]["pondID"]

        harvest_to_pond[
            harvest_id
        ] = pond_id


# ---------------------------------------------------------
# ProcessingLot -> Pond thông qua HarvestLot
# ---------------------------------------------------------

for event in business_events:

    if event["eventType"] == "PROCESSING":

        processing_id = (
            event["data"]["processingLotID"]
        )

        harvest_id = (
            event["data"]["harvestLotID"]
        )

        if harvest_id not in harvest_to_pond:
            raise ValueError(
                f"{event['eventID']}: "
                f"không tìm thấy lineage của "
                f"{harvest_id}"
            )

        processing_to_pond[
            processing_id
        ] = harvest_to_pond[
            harvest_id
        ]


# ---------------------------------------------------------
# Shipment -> Pond thông qua ProcessingLot
# ---------------------------------------------------------

for event in business_events:

    if event["eventType"] == "SHIPPING":

        shipment_id = (
            event["data"]["shipmentID"]
        )

        processing_id = (
            event["data"]["processingLotID"]
        )

        if processing_id not in processing_to_pond:
            raise ValueError(
                f"{event['eventID']}: "
                f"không tìm thấy lineage của "
                f"{processing_id}"
            )

        shipment_to_pond[
            shipment_id
        ] = processing_to_pond[
            processing_id
        ]


# ---------------------------------------------------------
# DistributionLot -> Pond thông qua Shipment
# ---------------------------------------------------------

for event in business_events:

    if event["eventType"] == "DISTRIBUTION":

        distribution_id = (
            event["data"]["distributionLotID"]
        )

        shipment_id = (
            event["data"]["shipmentID"]
        )

        if shipment_id not in shipment_to_pond:
            raise ValueError(
                f"{event['eventID']}: "
                f"không tìm thấy lineage của "
                f"{shipment_id}"
            )

        distribution_to_pond[
            distribution_id
        ] = shipment_to_pond[
            shipment_id
        ]


# ---------------------------------------------------------
# Xác định Pond gốc của từng sự kiện
# ---------------------------------------------------------

def get_event_pond(event):

    event_type = event["eventType"]
    data = event["data"]

    # Các sự kiện xảy ra trực tiếp tại ao
    if event_type in {
        "SEED_STOCKING",
        "FEEDING",
        "TREATMENT",
        "HARVEST",
    }:
        return data.get("pondID")

    # Processing truy ngược qua HarvestLot
    if event_type == "PROCESSING":
        harvest_id = data["harvestLotID"]
        return harvest_to_pond.get(
            harvest_id
        )

    # Shipping truy ngược qua ProcessingLot
    if event_type == "SHIPPING":
        processing_id = data[
            "processingLotID"
        ]
        return processing_to_pond.get(
            processing_id
        )

    # Distribution truy ngược qua Shipment
    if event_type == "DISTRIBUTION":
        shipment_id = data[
            "shipmentID"
        ]
        return shipment_to_pond.get(
            shipment_id
        )

    return None


# ---------------------------------------------------------
# Gom sự kiện theo lineage (Pond)
# ---------------------------------------------------------

events_by_pond = {}

for event in business_events:

    pond_id = get_event_pond(event)

    if pond_id is None:
        raise ValueError(
            f"{event['eventID']}: "
            f"không xác định được Pond lineage"
        )

    events_by_pond.setdefault(
        pond_id,
        []
    ).append(event)


# ---------------------------------------------------------
# Sắp xếp theo timestamp trong từng lineage
# và tạo hasPreviousEvent
# ---------------------------------------------------------

for pond_id, events in events_by_pond.items():

    events.sort(
        key=lambda e: (
            e["timestamp"],
            e["eventID"]
        )
    )

    previous_event_uri = None

    for event in events:

        event_uri = NS[
            f"TraceabilityEvent_{event['eventID']}"
        ]

        if previous_event_uri is not None:

            graph.add((
                event_uri,
                NS.hasPreviousEvent,
                previous_event_uri
            ))

        previous_event_uri = event_uri


# =========================================================
# 9. KIỂM TRA SAU MAPPING
# =========================================================

mapped_events = set(
    graph.subjects(
        RDF.type,
        NS.TraceabilityEvent
    )
)

if len(mapped_events) != expected_count:
    raise ValueError(
        f"Số TraceabilityEvent không khớp: "
        f"đầu vào {expected_count}, "
        f"sau mapping {len(mapped_events)}"
    )

if mapped_count != expected_count:
    raise ValueError(
        f"Đã mapping {mapped_count}/{expected_count} sự kiện."
    )


# ---------------------------------------------------------
# Kiểm tra performedBy
# ---------------------------------------------------------

events_with_actor = set(
    graph.subjects(
        NS.performedBy,
        None
    )
)

missing_actor_links = (
    mapped_events
    - events_with_actor
)

if missing_actor_links:
    raise ValueError(
        "Có sự kiện chưa liên kết actor: "
        f"{sorted(str(x) for x in missing_actor_links)}"
    )


# ---------------------------------------------------------
# Kiểm tra hasEvent
# ---------------------------------------------------------

events_with_owner = set(
    graph.objects(
        None,
        NS.hasEvent
    )
)

missing_owner_links = (
    mapped_events
    - events_with_owner
)

if missing_owner_links:
    raise ValueError(
        "Có sự kiện chưa liên kết lô nghiệp vụ: "
        f"{sorted(str(x) for x in missing_owner_links)}"
    )


# =========================================================
# 10. KIỂM TRA 7 EVENT SUBCLASS
# =========================================================

print()
print("EVENT SUBCLASS COUNTS:")

total_subclass_events = set()

for event_type, event_class in EVENT_CLASS.items():

    subclass_events = set(
        graph.subjects(
            RDF.type,
            event_class
        )
    )

    total_subclass_events.update(
        subclass_events
    )

    print(
        f"{event_type:<15} -> "
        f"{len(subclass_events)}"
    )


# Mỗi TraceabilityEvent phải thuộc đúng một trong 7 subclass
events_without_subclass = (
    mapped_events
    - total_subclass_events
)

if events_without_subclass:
    raise ValueError(
        "Có TraceabilityEvent chưa được gán Event subclass: "
        f"{sorted(str(x) for x in events_without_subclass)}"
    )


if total_subclass_events != mapped_events:
    raise ValueError(
        "Tập Event subclass không khớp với "
        f"{len(mapped_events)} TraceabilityEvent."
    )


# Kiểm tra một event có bị gán nhiều subclass hay không
for event_uri in mapped_events:

    event_subclasses = [
        event_class
        for event_class in EVENT_CLASS.values()
        if (
            event_uri,
            RDF.type,
            event_class
        ) in graph
    ]

    if len(event_subclasses) != 1:
        raise ValueError(
            f"{event_uri}: phải thuộc đúng 1 Event subclass, "
            f"hiện có {len(event_subclasses)}"
        )


print(
    "Total events with exactly one subclass:",
    len(total_subclass_events)
)


# =========================================================
# 11. KIỂM TRA hasPreviousEvent
# =========================================================

print()
print("BUSINESS EVENT CHAINS:")

for pond_id, events in sorted(
    events_by_pond.items()
):

    events.sort(
        key=lambda e: (
            e["timestamp"],
            e["eventID"]
        )
    )

    print(f"\n{pond_id}:")

    for i, event in enumerate(events):

        previous_id = (
            events[i - 1]["eventID"]
            if i > 0
            else "NONE"
        )

        print(
            f"{event['eventID']} | "
            f"{event['timestamp']} | "
            f"{event['eventType']} | "
            f"previous={previous_id}"
        )


# =========================================================
# 12. LƯU ONTOLOGY MỚI
# =========================================================

graph.serialize(
    destination=ONTOLOGY_OUTPUT,
    format="xml"
)


# =========================================================
# 13. KẾT QUẢ
# =========================================================

print()
print("=" * 60)
print("MAPPING SUCCESSFUL")
print("=" * 60)

print(
    "Mapped events:",
    mapped_count
)

print(
    "Total TraceabilityEvent:",
    len(mapped_events)
)

print(
    "Total events assigned to subclasses:",
    len(total_subclass_events)
)

print(
    "Output file:",
    ONTOLOGY_OUTPUT
)