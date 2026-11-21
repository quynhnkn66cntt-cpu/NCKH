from pathlib import Path
import json
import hashlib
import yaml

# ==========================================
# 1. Load configuration
# ==========================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])

INPUT_DIR = BASE_DIR / config["paths"]["payloads"]
OUTPUT_DIR = BASE_DIR / config["paths"]["hashed_events"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. Hàm tạo SHA-256
# ==========================================

def sha256_text(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


# ==========================================
# 3. Đọc toàn bộ event
# ==========================================

files = sorted(
    INPUT_DIR.glob("EV*.json"),
    key=lambda x: int(x.stem.replace("EV", ""))
)

print("==========================================")
print("TAO HASH CHO TRACEABILITY EVENTS")
print("==========================================")

print("Thu muc input:", INPUT_DIR)
print("So file:", len(files))

if not files:
    raise ValueError(
        f"Khong tim thay file event nao trong {INPUT_DIR}."
    )
# ==========================================
# 4. Tạo hash cho từng event
# ==========================================

previous_event_hash = "GENESIS"

for file in files:

    # --------------------------------------
    # Đọc JSON
    # --------------------------------------

    with open(file, "r", encoding="utf-8") as f:
        event = json.load(f)

    event_id = str(event["eventID"]).strip()
    batch_id = str(event["batchID"]).strip()
    event_type = str(event["eventType"]).strip()
    actor_id = str(event["actorID"]).strip()
    timestamp = str(event["timestamp"]).strip()

    # --------------------------------------
    # Tạo chuỗi ổn định từ data
    # --------------------------------------

    data_string = json.dumps(
        event["data"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )

    # --------------------------------------
    # Tạo dataHash
    # --------------------------------------

    data_hash = sha256_text(data_string)

    # --------------------------------------
    # previousEventHash
    # --------------------------------------

    current_previous_hash = previous_event_hash

    # --------------------------------------
    # Tạo currentHash
    # --------------------------------------

    hash_content = (
        event_id
        + "|"
        + batch_id
        + "|"
        + event_type
        + "|"
        + actor_id
        + "|"
        + timestamp
        + "|"
        + data_hash
        + "|"
        + current_previous_hash
    )

    current_hash = sha256_text(hash_content)

    # --------------------------------------
    # Thêm hash vào event
    # --------------------------------------

    event["dataHash"] = data_hash
    event["previousEventHash"] = current_previous_hash
    event["currentHash"] = current_hash

    # --------------------------------------
    # Ghi file mới
    # --------------------------------------

    output_file = OUTPUT_DIR / file.name

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            event,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(
        f"Da hash {event_id}: "
        f"{event_type}"
    )

    # Event hiện tại trở thành event trước
    previous_event_hash = current_hash


# ==========================================
# 5. Hoàn thành
# ==========================================

print("\n==========================================")
print("HOAN THANH TAO HASH")
print("==========================================")

print("Tong so event:", len(files))
print("Thu muc output:", OUTPUT_DIR)
print("Hash dau tien:", "GENESIS")
print("Hash cuoi cung:", previous_event_hash)

print("\n>>> TAO HASH THANH CONG <<<")