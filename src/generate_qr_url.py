from pathlib import Path
import yaml
import qrcode

# ============================================================
# LOAD CONFIG
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
BASE_URL = config["demo"]["base_url"].rstrip("/")
OUTPUT_DIR = BASE_DIR / config["paths"]["qr_urls"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# GENERATE URL QR CODES
# ============================================================

distribution_lots = [
    "DL001",
    "DL002",
    "DL003",
    "DL004",
    "DL005"
]

for lot_id in distribution_lots:

    trace_url = f"{BASE_URL}/?lot={lot_id}"

    img = qrcode.make(trace_url)

    output_file = OUTPUT_DIR / f"{lot_id}_url.png"
    img.save(output_file)

    print(f"{lot_id} -> {trace_url}")
    print(f"       -> {output_file}")

print("\nGenerated:", len(distribution_lots), "URL QR codes")