import json
import hashlib
import copy
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

OFFCHAIN_DIR = BASE_DIR / config["paths"]["hashed_events"]
BLOCKCHAIN_DIR = BASE_DIR / config["paths"]["ledger_events"]

def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def calculate_hashes(event):
    data_string = json.dumps(
        event["data"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )

    data_hash = sha256_text(data_string)

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
        + data_hash
        + "|"
        + str(event["previousEventHash"]).strip()
    )

    current_hash = sha256_text(hash_content)

    return data_hash, current_hash


total = 0
detected = 0
not_detected = 0

for offchain_file in sorted(OFFCHAIN_DIR.glob("EV*.json")):

    event_id = offchain_file.stem
    blockchain_file = BLOCKCHAIN_DIR / f"{event_id}.json"

    with open(offchain_file, "r", encoding="utf-8") as f:
        original = json.load(f)

    with open(blockchain_file, "r", encoding="utf-8") as f:
        blockchain = json.load(f)

    # Chỉ giả mạo bản sao trong RAM
    tampered = copy.deepcopy(original)

    # Thêm một trường giả mạo vào phần data.
    # Không sửa file JSON gốc.
    tampered["data"]["tampered_test"] = "MODIFIED"

    tampered_data_hash, tampered_current_hash = calculate_hashes(tampered)

    total += 1

    is_detected = (
        tampered_data_hash != blockchain["dataHash"]
        or tampered_current_hash != blockchain["currentHash"]
    )

    if is_detected:
        detected += 1
    else:
        not_detected += 1
        print(f"NOT DETECTED: {event_id}")


detection_rate = (detected / total * 100) if total else 0


print("\n========================================")
print("TAMPERING DETECTION EXPERIMENT")
print("========================================")
print("Tampered events tested :", total)
print("Tampering detected     :", detected)
print("Not detected           :", not_detected)
print(f"Detection rate         : {detection_rate:.2f}%")

if detected == total and not_detected == 0:
    print("\nPASS: ALL TAMPERING CASES WERE DETECTED.")
else:
    print("\nFAIL: SOME TAMPERING CASES WERE NOT DETECTED.")

print("\nOriginal files were NOT modified.")