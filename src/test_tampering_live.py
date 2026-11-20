import copy
import json
from collections import defaultdict

from verify_live import OFFCHAIN_DIR, calculate_hashes, get_live_event


def load_events():
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(OFFCHAIN_DIR.glob("EV*.json"))
    ]


def change_value(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    return str(value) + "_MODIFIED"


def make_cases(events):
    cases = []

    for original in events:
        event_id = original["eventID"]
        data = original.get("data", {})

        if "quantity" in data:
            modified = copy.deepcopy(original)
            modified["data"]["quantity"] = change_value(data["quantity"])
            cases.append(("QUANTITY", event_id, modified))

        if "dosage" in data:
            modified = copy.deepcopy(original)
            modified["data"]["dosage"] = change_value(data["dosage"])
            cases.append(("DOSAGE", event_id, modified))

        for field in ("timestamp", "actorID", "previousEventHash"):
            modified = copy.deepcopy(original)
            modified[field] = change_value(original[field])
            cases.append((field.upper(), event_id, modified))

        if data:
            modified = copy.deepcopy(original)
            first_key = next(iter(data))
            del modified["data"][first_key]
            cases.append(("DELETE_FIELD", event_id, modified))

        modified = copy.deepcopy(original)
        modified["data"] = {
            "replacedPayload": True,
            "source": "tampering_test"
        }
        cases.append(("REPLACE_PAYLOAD", event_id, modified))

    return cases


def detected_by_fabric(modified, blockchain):
    data_hash, current_hash = calculate_hashes(modified)

    identity_fields = (
        "eventID", "batchID", "eventType", "actorID",
        "timestamp", "previousEventHash"
    )

    return (
        data_hash != blockchain.get("dataHash")
        or current_hash != blockchain.get("currentHash")
        or any(
            modified.get(field) != blockchain.get(field)
            for field in identity_fields
        )
    )


def main():
    events = load_events()
    print("Original events:", len(events), flush=True)

    if len(events) != 116:
        print("WARNING: Dataset size differs from previous experiment.")

    ledger = {}

    # Truy vấn trực tiếp Fabric trước khi thử nghiệm.
    # Nếu có lỗi truy vấn, không tính thành phát hiện giả mạo.
    for event in events:
        event_id = event["eventID"]

        try:
            ledger[event_id] = get_live_event(event_id)
        except Exception as exc:
            print(f"FABRIC QUERY ERROR {event_id}: {exc}", flush=True)

    print("Fabric records retrieved:", len(ledger), flush=True)

    if len(ledger) != len(events):
        print("ABORTED: Could not retrieve all Fabric records.")
        return

    # Kiểm tra dữ liệu gốc trước khi tạo các bản giả mạo.
    for event in events:
        if detected_by_fabric(event, ledger[event["eventID"]]):
            print("ABORTED: Original event mismatch:", event["eventID"])
            return

    results = defaultdict(lambda: {"total": 0, "detected": 0})

    for case_type, event_id, modified in make_cases(events):
        results[case_type]["total"] += 1

        if detected_by_fabric(modified, ledger[event_id]):
            results[case_type]["detected"] += 1
        else:
            print(f"NOT DETECTED: {case_type} {event_id}")

    print("\nLIVE FABRIC TAMPERING TEST RESULTS")
    print("=" * 65)
    print(f"{'Case':22} {'Tested':>8} {'Detected':>10} {'Rate':>10}")
    print("-" * 65)

    total = 0
    detected = 0

    for case_type, values in results.items():
        n = values["total"]
        d = values["detected"]
        rate = d / n * 100 if n else 0

        print(f"{case_type:22} {n:8} {d:10} {rate:9.2f}%")
        total += n
        detected += d

    print("-" * 65)
    rate = detected / total * 100 if total else 0
    print(f"{'TOTAL':22} {total:8} {detected:10} {rate:9.2f}%")
    print("\nOriginal JSON files were NOT modified.")
    print("No blockchain transactions were submitted.")


if __name__ == "__main__":
    main()
