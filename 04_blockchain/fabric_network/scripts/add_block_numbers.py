import csv
import json
import subprocess
from pathlib import Path

NETWORK = Path.home() / "nckh-blockchain/traceability-network"
INPUT = NETWORK / "results/blockchain_metadata.csv"
OUTPUT = NETWORK / "results/blockchain_metadata_with_blocks.csv"
TMP = Path("/tmp/nckh_blocks")

CHANNEL = "traceabilitychannel"
ORDERER = "orderer.example.com:7050"
CAFILE = (
    NETWORK
    / "organizations/ordererOrganizations/example.com/orderers/"
      "orderer.example.com/tls/ca.crt"
)

TMP.mkdir(exist_ok=True)

with open(INPUT, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

tx_to_row = {r["txId"]: r for r in rows}
found = {}

# Lấy chiều cao ledger
info = subprocess.run(
    ["peer", "channel", "getinfo", "-c", CHANNEL],
    cwd=NETWORK,
    text=True,
    capture_output=True,
    check=True
)

text = info.stdout + info.stderr
start = text.find('{"height"')
end = text.find("}", start) + 1

ledger_info = json.loads(text[start:end])
height = int(ledger_info["height"])

print(f"Ledger height: {height}")
print(f"Can tim: {len(tx_to_row)} transaction")

# Quét block 0 -> height-1
for block_num in range(height):
    pb = TMP / f"block_{block_num}.pb"
    js = TMP / f"block_{block_num}.json"

    subprocess.run(
        [
            "peer", "channel", "fetch", str(block_num), str(pb),
            "-o", ORDERER,
            "-c", CHANNEL,
            "--tls",
            "--cafile", str(CAFILE)
        ],
        cwd=NETWORK,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    subprocess.run(
        [
            "configtxlator", "proto_decode",
            "--input", str(pb),
            "--type", "common.Block",
            "--output", str(js)
        ],
        cwd=NETWORK,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    with open(js, encoding="utf-8") as f:
        block = json.load(f)

    # Tìm mọi tx_id trong block
    def walk(obj):
        if isinstance(obj, dict):
            txid = obj.get("tx_id")
            if txid in tx_to_row:
                found[txid] = block_num

            for value in obj.values():
                walk(value)

        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(block)

    print(
        f"Block {block_num}/{height - 1} | "
        f"found {len(found)}/{len(tx_to_row)}"
    )

    if len(found) == len(tx_to_row):
        break

for row in rows:
    row["blockNumber"] = (
        str(found[row["txId"]])
        if row["txId"] in found
        else ""
    )

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "eventID",
            "batchID",
            "eventType",
            "msp",
            "txId",
            "blockNumber"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

missing = [r["eventID"] for r in rows if not r["blockNumber"]]

print("=" * 60)
print(f"Tim thay: {len(rows) - len(missing)}/{len(rows)}")
print(f"Thieu blockNumber: {missing}")
print(f"Output: {OUTPUT}")
