import csv
import statistics
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
INPUT = BASE_DIR / config["paths"]["write_performance"]

# ============================================================
# ANALYZE WRITE PERFORMANCE
# ============================================================

times = []
valid = 0
failed = 0

with open(INPUT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["status"] == "VALID":
            times.append(float(row["time_ms"]))
            valid += 1
        else:
            failed += 1

print("========================================")
print("BLOCKCHAIN WRITE PERFORMANCE")
print("========================================")
print("Input file          :", INPUT)
print("Transactions tested :", valid + failed)
print("Valid transactions  :", valid)
print("Failed transactions :", failed)
print(f"Minimum time        : {min(times):.2f} ms")
print(f"Maximum time        : {max(times):.2f} ms")
print(f"Average time        : {statistics.mean(times):.2f} ms")
print(f"Median time         : {statistics.median(times):.2f} ms")
print(f"Std deviation       : {statistics.stdev(times):.2f} ms")
print(f"Success rate        : {valid / (valid + failed) * 100:.2f}%")