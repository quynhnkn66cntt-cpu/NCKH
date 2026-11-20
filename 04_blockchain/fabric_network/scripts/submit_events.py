import os
import json
import subprocess
import re
import csv
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

NETWORK_DIR = Path.home() / "nckh-blockchain" / "traceability-network"

EVENT_DIR_ENV = os.environ.get("TRACEABILITY_EVENT_DIR")

if not EVENT_DIR_ENV:
    raise RuntimeError(
        "TRACEABILITY_EVENT_DIR is not set. "
        "Set it to the hashed_events directory."
    )

EVENT_DIR = Path(EVENT_DIR_ENV)

OUTPUT_DIR = NETWORK_DIR / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RESULT_FILE = OUTPUT_DIR / "blockchain_transactions.csv"
LOG_FILE = OUTPUT_DIR / "submit_events.log"

CHANNEL = "traceabilitychannel"
CHAINCODE = "traceability"

ORDERER = "orderer.example.com:7050"

ORDERER_CA = (
    NETWORK_DIR
    / "organizations/ordererOrganizations/example.com/"
      "orderers/orderer.example.com/tls/ca.crt"
)

PEERS = [
    (
        "peer0.farm.example.com:7051",
        NETWORK_DIR
        / "organizations/peerOrganizations/farm.example.com/"
          "peers/peer0.farm.example.com/tls/ca.crt"
    ),
    (
        "peer0.processing.example.com:8051",
        NETWORK_DIR
        / "organizations/peerOrganizations/processing.example.com/"
          "peers/peer0.processing.example.com/tls/ca.crt"
    ),
    (
        "peer0.distribution.example.com:9051",
        NETWORK_DIR
        / "organizations/peerOrganizations/distribution.example.com/"
          "peers/peer0.distribution.example.com/tls/ca.crt"
    )
]

MSP_CONFIG = {
    "FarmMSP": {
        "msp_path": NETWORK_DIR
        / "organizations/peerOrganizations/farm.example.com/"
          "users/Admin@farm.example.com/msp",

        "address": "peer0.farm.example.com:7051",

        "tls_cert": NETWORK_DIR
        / "organizations/peerOrganizations/farm.example.com/"
          "peers/peer0.farm.example.com/tls/ca.crt"
    },

    "ProcessingMSP": {
        "msp_path": NETWORK_DIR
        / "organizations/peerOrganizations/processing.example.com/"
          "users/Admin@processing.example.com/msp",

        "address": "peer0.processing.example.com:8051",

        "tls_cert": NETWORK_DIR
        / "organizations/peerOrganizations/processing.example.com/"
          "peers/peer0.processing.example.com/tls/ca.crt"
    },

    "DistributionMSP": {
        "msp_path": NETWORK_DIR
        / "organizations/peerOrganizations/distribution.example.com/"
          "users/Admin@distribution.example.com/msp",

        "address": "peer0.distribution.example.com:9051",

        "tls_cert": NETWORK_DIR
        / "organizations/peerOrganizations/distribution.example.com/"
          "peers/peer0.distribution.example.com/tls/ca.crt"
    }
}

EVENT_MSP = {
    "SEED_STOCKING": "FarmMSP",
    "FEEDING": "FarmMSP",
    "TREATMENT": "FarmMSP",
    "HARVEST": "FarmMSP",

    "PROCESSING": "ProcessingMSP",

    "SHIPPING": "DistributionMSP",
    "DISTRIBUTION": "DistributionMSP"
}


# ============================================================
# LOG
# ============================================================

def log(message):
    now = datetime.now().isoformat(timespec="seconds")
    line = f"[{now}] {message}"

    print(line)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# ENVIRONMENT
# ============================================================

def get_env(msp):
    import os

    env = os.environ.copy()

    config = MSP_CONFIG[msp]

    env["CORE_PEER_TLS_ENABLED"] = "true"
    env["CORE_PEER_LOCALMSPID"] = msp
    env["CORE_PEER_MSPCONFIGPATH"] = str(config["msp_path"])
    env["CORE_PEER_ADDRESS"] = config["address"]
    env["CORE_PEER_TLS_ROOTCERT_FILE"] = str(config["tls_cert"])

    return env


# ============================================================
# RUN COMMAND
# ============================================================

def run_command(command, env):
    result = subprocess.run(
        command,
        cwd=NETWORK_DIR,
        env=env,
        text=True,
        capture_output=True
    )

    output = (result.stdout or "") + (result.stderr or "")

    return result.returncode, output


# ============================================================
# CHECK EVENT
# ============================================================

def event_exists(event_id, msp):
    env = get_env(msp)

    payload = {
        "Args": [
            "EventExists",
            event_id
        ]
    }

    command = [
        "peer", "chaincode", "query",
        "-C", CHANNEL,
        "-n", CHAINCODE,
        "-c", json.dumps(payload)
    ]

    code, output = run_command(command, env)

    if code != 0:
        raise RuntimeError(
            f"Cannot check {event_id}: {output}"
        )

    return output.strip().lower() == "true"


# ============================================================
# SUBMIT EVENT
# ============================================================

def submit_event(event, msp):
    env = get_env(msp)

    args = [
        "CreateEvent",
        str(event["eventID"]),
        str(event["batchID"]),
        str(event["eventType"]),
        str(event["actorID"]),
        str(event["dataHash"]),
        str(event["currentHash"]),
        str(event["previousEventHash"]),
        str(event["timestamp"]),
        str(event.get("documentURI", ""))
    ]

    payload = {
        "Args": args
    }

    command = [
        "peer", "chaincode", "invoke",

        "-o", ORDERER,

        "--ordererTLSHostnameOverride",
        "orderer.example.com",

        "--tls",

        "--cafile",
        str(ORDERER_CA),

        "-C", CHANNEL,

        "-n", CHAINCODE
    ]

    # Endorse using all three peers
    for peer_address, tls_cert in PEERS:

        command.extend([
            "--peerAddresses",
            peer_address,

            "--tlsRootCertFiles",
            str(tls_cert)
        ])

    command.extend([
        "-c",
        json.dumps(payload),

        "--waitForEvent"
    ])

    start = time.perf_counter()

    code, output = run_command(command, env)

    elapsed = time.perf_counter() - start

    tx_match = re.search(
        r"txid \[([a-fA-F0-9]+)\]",
        output
    )

    tx_id = tx_match.group(1) if tx_match else ""

    valid = (
        code == 0
        and "status (VALID)" in output
        and "status:200" in output
    )

    return {
        "success": valid,
        "txId": tx_id,
        "elapsedSeconds": round(elapsed, 4),
        "output": output
    }


# ============================================================
# SAVE RESULT
# ============================================================
def save_result(row):
    fieldnames = [
        "eventID",
        "batchID",
        "eventType",
        "msp",
        "status",
        "txId",
        "elapsedSeconds"
    ]

    rows = []

    if RESULT_FILE.exists():
        with open(
            RESULT_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as f:
            rows = list(csv.DictReader(f))

    # Không tạo thêm bản ghi nếu eventID đã có trong CSV.
    if any(r["eventID"] == row["eventID"] for r in rows):
        return

    rows.append(row)

    with open(
        RESULT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    files = sorted(
        EVENT_DIR.glob("*.json"),
        key=lambda p: int(p.stem.replace("EV", ""))
    )

    log(f"Found {len(files)} event files.")

    success = 0
    skipped = 0
    failed = 0

    for index, file in enumerate(files, start=1):

        try:

            with open(file, encoding="utf-8") as f:
                event = json.load(f)

            event_id = event["eventID"]
            event_type = event["eventType"]

            msp = EVENT_MSP.get(event_type)

            if not msp:
                log(
                    f"[{index}/{len(files)}] "
                    f"{event_id} UNKNOWN EVENT TYPE: "
                    f"{event_type}"
                )

                failed += 1
                continue

            log(
                f"[{index}/{len(files)}] "
                f"{event_id} "
                f"{event_type} -> {msp}"
            )

            # Skip events already committed
            if event_exists(event_id, msp):

                log(
                    f"{event_id} already exists -> SKIP"
                )

                save_result({
                    "eventID": event_id,
                    "batchID": event["batchID"],
                    "eventType": event_type,
                    "msp": msp,
                    "status": "SKIPPED_EXISTS",
                    "txId": "",
                    "elapsedSeconds": ""
                })

                skipped += 1
                continue

            result = submit_event(event, msp)

            if result["success"]:

                log(
                    f"{event_id} VALID "
                    f"txId={result['txId']} "
                    f"time={result['elapsedSeconds']}s"
                )

                status = "VALID"
                success += 1

            else:

                log(
                    f"{event_id} FAILED\n"
                    f"{result['output']}"
                )

                status = "FAILED"
                failed += 1

            save_result({
                "eventID": event_id,
                "batchID": event["batchID"],
                "eventType": event_type,
                "msp": msp,
                "status": status,
                "txId": result["txId"],
                "elapsedSeconds": result["elapsedSeconds"]
            })

        except Exception as e:

            log(
                f"{file.name} ERROR: {e}"
            )

            failed += 1

    log("=" * 60)

    log(
        f"Finished | "
        f"VALID={success} "
        f"SKIPPED={skipped} "
        f"FAILED={failed}"
    )


if __name__ == "__main__":
    main()
