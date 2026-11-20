import json
import hashlib
import copy
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

OFFCHAIN_FILE = (
    BASE_DIR
    / config["paths"]["hashed_events"]
    / "EV001.json"
)

BLOCKCHAIN_FILE = BASE_DIR / config["paths"]["blockchain_ev001"]


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


with open(OFFCHAIN_FILE, "r", encoding="utf-8") as f:
    offchain = json.load(f)

with open(BLOCKCHAIN_FILE, "r", encoding="utf-8") as f:
    blockchain = json.load(f)


# ==================================================
# TEST 1: Dữ liệu off-chain nguyên vẹn
# ==================================================

data_hash, current_hash = calculate_hashes(offchain)

print("========================================")
print("TEST 1: ORIGINAL OFF-CHAIN DATA")
print("========================================")

print("Event:", offchain["eventID"])
print("Blockchain txId:", blockchain["txId"])
print("Created by MSP:", blockchain["createdByMSP"])

print("\nCalculated dataHash :", data_hash)
print("Blockchain dataHash :", blockchain["dataHash"])

print("\nCalculated currentHash :", current_hash)
print("Blockchain currentHash :", blockchain["currentHash"])

original_valid = (
    data_hash == blockchain["dataHash"]
    and current_hash == blockchain["currentHash"]
)

if original_valid:
    print("\nPASS: OFF-CHAIN DATA MATCHES BLOCKCHAIN.")
else:
    print("\nFAIL: OFF-CHAIN DATA DOES NOT MATCH BLOCKCHAIN.")


# ==================================================
# TEST 2: Giả mạo dữ liệu trong RAM
# ==================================================

tampered = copy.deepcopy(offchain)

original_quantity = tampered["data"]["quantity"]
tampered["data"]["quantity"] = 999999

tampered_data_hash, tampered_current_hash = calculate_hashes(tampered)

print("\n========================================")
print("TEST 2: TAMPERED OFF-CHAIN DATA")
print("========================================")

print("Original quantity:", original_quantity)
print("Tampered quantity:", tampered["data"]["quantity"])

print("\nTampered dataHash   :", tampered_data_hash)
print("Blockchain dataHash :", blockchain["dataHash"])

print("\nTampered currentHash   :", tampered_current_hash)
print("Blockchain currentHash :", blockchain["currentHash"])

tampering_detected = (
    tampered_data_hash != blockchain["dataHash"]
    or tampered_current_hash != blockchain["currentHash"]
)

if tampering_detected:
    print("\nPASS: TAMPERING DETECTED BY BLOCKCHAIN HASH COMPARISON.")
else:
    print("\nFAIL: TAMPERING WAS NOT DETECTED.")

print("\nOriginal EV001 file was NOT modified.")