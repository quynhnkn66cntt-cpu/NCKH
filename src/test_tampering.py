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

EVENT_FILE = BASE_DIR / config["paths"]["hashed_events"] / "EV001.json"

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


with open(EVENT_FILE, "r", encoding="utf-8") as f:
    original = json.load(f)

# Chỉ tạo bản sao trong RAM
tampered = copy.deepcopy(original)

print("================================")
print("TAMPERING TEST:", original["eventID"])
print("================================")

print("\nOriginal quantity:",
      original["data"]["quantity"])

# Giả mạo dữ liệu
tampered["data"]["quantity"] = 999999

print("Tampered quantity:",
      tampered["data"]["quantity"])

# Tính lại hash từ dữ liệu đã bị sửa
new_data_hash, new_current_hash = calculate_hashes(tampered)

print("\nStored dataHash    :", original["dataHash"])
print("Calculated dataHash:", new_data_hash)

print("\nStored currentHash    :", original["currentHash"])
print("Calculated currentHash:", new_current_hash)

data_match = new_data_hash == original["dataHash"]
current_match = new_current_hash == original["currentHash"]

print("\nDataHash match   :", data_match)
print("CurrentHash match:", current_match)

if not data_match and not current_match:
    print("\nPASS: TAMPERING DETECTED.")
else:
    print("\nFAIL: Tampering was not detected.")

print("\nOriginal EV001 file was NOT modified.")