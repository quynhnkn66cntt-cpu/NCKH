import json
import hashlib
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
valid = 0
invalid = 0
missing = 0

for offchain_file in sorted(OFFCHAIN_DIR.glob("EV*.json")):

    event_id = offchain_file.stem
    blockchain_file = BLOCKCHAIN_DIR / f"{event_id}.json"

    total += 1

    if not blockchain_file.exists():
        print(f"MISSING BLOCKCHAIN RECORD: {event_id}")
        missing += 1
        continue

    with open(offchain_file, "r", encoding="utf-8") as f:
        offchain = json.load(f)

    with open(blockchain_file, "r", encoding="utf-8") as f:
        blockchain = json.load(f)

    calculated_data_hash, calculated_current_hash = calculate_hashes(offchain)

    data_ok = calculated_data_hash == blockchain["dataHash"]
    current_ok = calculated_current_hash == blockchain["currentHash"]

    if data_ok and current_ok:
        valid += 1
    else:
        invalid += 1
        print(f"INVALID: {event_id}")

        if not data_ok:
            print("  dataHash mismatch")

        if not current_ok:
            print("  currentHash mismatch")


integrity_rate = (valid / total * 100) if total else 0


print("\n========================================")
print("BLOCKCHAIN INTEGRITY VERIFICATION")
print("========================================")
print("Total events checked :", total)
print("Valid                :", valid)
print("Invalid              :", invalid)
print("Missing on blockchain:", missing)
print(f"Integrity rate       : {integrity_rate:.2f}%")

if valid == total and invalid == 0 and missing == 0:
    print("\nPASS: ALL OFF-CHAIN EVENTS MATCH BLOCKCHAIN.")
else:
    print("\nFAIL: INTEGRITY PROBLEM DETECTED.")
