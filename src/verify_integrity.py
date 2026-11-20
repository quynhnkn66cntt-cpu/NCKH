import json
import hashlib
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

EVENT_DIR = BASE_DIR / config["paths"]["hashed_events"]
def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def calculate_hashes(event):
    # Tạo chuỗi data giống chính xác hashed_events.py
    data_string = json.dumps(
        event["data"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )

    calculated_data_hash = sha256_text(data_string)

    hash_content = (
        str(event["eventID"]).strip()
        + "|"
        + str(event["batchID"]).strip()
        + "|"
        + str(event["eventType"]).strip()
        + "|"
        + str(event["actorID"]).strip()
        + "|"
        + str(event["timestamp"]).strip()
        + "|"
        + calculated_data_hash
        + "|"
        + str(event["previousEventHash"]).strip()
    )

    calculated_current_hash = sha256_text(hash_content)

    return calculated_data_hash, calculated_current_hash


total = 0
valid = 0
invalid = 0

for file in sorted(EVENT_DIR.glob("EV*.json")):
    with open(file, "r", encoding="utf-8") as f:
        event = json.load(f)

    total += 1

    calculated_data_hash, calculated_current_hash = calculate_hashes(event)

    data_ok = calculated_data_hash == event["dataHash"]
    current_ok = calculated_current_hash == event["currentHash"]

    if data_ok and current_ok:
        valid += 1
    else:
        invalid += 1
        print(f"\nFAIL: {event['eventID']}")

        if not data_ok:
            print("  dataHash mismatch")

        if not current_ok:
            print("  currentHash mismatch")


print("\n==============================")
print("INTEGRITY VERIFICATION RESULT")
print("==============================")
print("Total events :", total)
print("VALID        :", valid)
print("INVALID      :", invalid)

if invalid == 0 and total > 0:
    print("\nPASS: All events are intact.")
else:
    print("\nFAIL: Data tampering or hash mismatch detected.")