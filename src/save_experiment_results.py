import csv
from pathlib import Path
import yaml

# ============================================================
# LOAD CONFIG
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
OUTPUT = BASE_DIR / config["paths"]["experiment_summary"]

# ============================================================
# SAVE EXPERIMENT RESULTS
# ============================================================

rows = [
    [
        "Metric",
        "Total",
        "Success",
        "Failure",
        "Rate",
        "Min_ms",
        "Max_ms",
        "Average_ms",
        "Median_ms",
        "StdDev_ms",
    ],
    [
        "Blockchain integrity verification",
        116, 116, 0, "100.00%",
        "", "", "", "", "",
    ],
    [
        "Tampering detection",
        116, 116, 0, "100.00%",
        "", "", "", "", "",
    ],
    [
        "Blockchain query performance",
        30, 30, 0, "100.00%",
        "77.00", "108.00", "86.57", "86.00", "6.43",
    ],
    [
        "Blockchain write commit performance",
        30, 30, 0, "100.00%",
        "2173.00", "2306.00", "2207.07", "2201.00", "28.23",
    ],
]

with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print("Saved:", OUTPUT)