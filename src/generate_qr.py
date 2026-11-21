from pathlib import Path
import yaml
import qrcode

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
OUTPUT_DIR = BASE_DIR / config["paths"]["qr_codes"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
distribution_lots = [
    "DL001",
    "DL002",
    "DL003",
    "DL004",
    "DL005"
]

for lot_id in distribution_lots:
    qr_data = lot_id

    img = qrcode.make(qr_data)

    output_file = OUTPUT_DIR / f"{lot_id}.png"
    img.save(output_file)

    print(f"{lot_id} -> {output_file}")

print("\nGenerated:", len(distribution_lots), "QR codes")