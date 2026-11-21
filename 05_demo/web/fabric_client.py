import os
import json
import subprocess
from pathlib import Path

NETWORK_DIR = Path.home() / "nckh-blockchain" / "traceability-network"
FABRIC_HOME = Path.home() / "nckh-blockchain"

ORG_DIR = (
    NETWORK_DIR
    / "organizations/peerOrganizations/distribution.example.com"
)

PEER_BIN = FABRIC_HOME / "bin/peer"


def get_blockchain_event(event_id):
    """Đọc sự kiện trực tiếp từ Hyperledger Fabric."""

    env = os.environ.copy()

    env["PATH"] = str(FABRIC_HOME / "bin") + os.pathsep + env.get("PATH", "")
    env["FABRIC_CFG_PATH"] = str(FABRIC_HOME / "config")
    env["CORE_PEER_TLS_ENABLED"] = "true"
    env["CORE_PEER_LOCALMSPID"] = "DistributionMSP"
    env["CORE_PEER_MSPCONFIGPATH"] = str(
        ORG_DIR / "users/Admin@distribution.example.com/msp"
    )
    env["CORE_PEER_ADDRESS"] = "peer0.distribution.example.com:9051"
    env["CORE_PEER_TLS_ROOTCERT_FILE"] = str(
        ORG_DIR / "peers/peer0.distribution.example.com/tls/ca.crt"
    )
    env.pop("CORE_PEER_TLS_SERVERHOSTOVERRIDE", None)

    command = [
        str(PEER_BIN),
        "chaincode", "query",
        "-C", "traceabilitychannel",
        "-n", "traceability",
        "-c", json.dumps({
            "function": "GetEvent",
            "Args": [event_id]
        })
    ]

    result = subprocess.run(
        command,
        cwd=NETWORK_DIR,
        env=env,
        text=True,
        capture_output=True,
        timeout=15
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "Blockchain query failed"
        )

    return json.loads(result.stdout)


if __name__ == "__main__":
    event = get_blockchain_event("EV112")
    print(json.dumps(event, indent=2, ensure_ascii=False))
