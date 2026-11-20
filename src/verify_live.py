import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

OFFCHAIN_DIR = Path(
    "/mnt/d/NCKH/02_preprocessed/mapped/hashed_events"
)

NETWORK_DIR = Path.home() / "nckh-blockchain" / "traceability-network"

CHANNEL = "traceabilitychannel"
CHAINCODE = "traceability"


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

    hash_content = "|".join([
        str(event["eventID"]).strip(),
        str(event["batchID"]).strip(),
        str(event["eventType"]).strip(),
        str(event["actorID"]).strip(),
        str(event["timestamp"]).strip(),
        data_hash,
        str(event["previousEventHash"]).strip()
    ])

    current_hash = sha256_text(hash_content)

    return data_hash, current_hash


def get_live_event(event_id):
    command = [
        str(Path.home() / "nckh-blockchain/bin/peer"),
        "chaincode", "query",
        "-C", CHANNEL,
        "-n", CHAINCODE,
        "-c", json.dumps({
            "Args": ["GetEvent", event_id]
        })
    ]

    env = os.environ.copy()

    result = subprocess.run(
        command,
        cwd=NETWORK_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return json.loads(result.stdout)


def verify_event(event_id):
    offchain_file = OFFCHAIN_DIR / f"{event_id}.json"

    if not offchain_file.exists():
        print(f"OFFCHAIN FILE NOT FOUND: {event_id}")
        return False

    with open(offchain_file, encoding="utf-8") as f:
        offchain = json.load(f)

    calculated_data_hash, calculated_current_hash = (
        calculate_hashes(offchain)
    )

    try:
        blockchain = get_live_event(event_id)
    except Exception as e:
        print(f"FABRIC QUERY ERROR: {e}")
        return False

    data_ok = (
        calculated_data_hash == blockchain.get("dataHash")
    )

    current_ok = (
        calculated_current_hash == blockchain.get("currentHash")
    )

    identity_ok = (
        offchain.get("eventID") == blockchain.get("eventID")
        and offchain.get("batchID") == blockchain.get("batchID")
        and offchain.get("eventType") == blockchain.get("eventType")
        and offchain.get("actorID") == blockchain.get("actorID")
        and offchain.get("timestamp") == blockchain.get("timestamp")
        and offchain.get("previousEventHash")
        == blockchain.get("previousEventHash")
    )

    print("\n====================================")
    print("LIVE FABRIC INTEGRITY VERIFICATION")
    print("====================================")
    print("Event ID:", event_id)
    print("Fabric txId:", blockchain.get("txId"))
    print("dataHash match:", data_ok)
    print("currentHash match:", current_ok)
    print("Event fields match:", identity_ok)

    if data_ok and current_ok and identity_ok:
        print("\nVALID: Off-chain event matches live Fabric ledger.")
        return True

    print("\nTAMPERED: Off-chain event does not match Fabric ledger.")
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        files = sorted(OFFCHAIN_DIR.glob("EV*.json"))

        total = len(files)
        valid = 0
        invalid = 0

        if total == 0:
            print("ERROR: No off-chain events found.")
            sys.exit(1)

        for index, file in enumerate(files, start=1):
            print(f"\n[{index}/{total}] Checking {file.stem}")

            if verify_event(file.stem):
                valid += 1
            else:
                invalid += 1

        print("\n====================================")
        print("LIVE FABRIC VERIFICATION SUMMARY")
        print("====================================")
        print("Total events :", total)
        print("Valid        :", valid)
        print("Invalid/error:", invalid)
        print(f"Integrity rate: {valid / total * 100:.2f}%")

        sys.exit(0 if invalid == 0 else 1)

    else:
        event_id = sys.argv[1] if len(sys.argv) > 1 else "EV001"
        success = verify_event(event_id)
        sys.exit(0 if success else 1)