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
INPUT = BASE_DIR / config["paths"]["query_performance"]

# ============================================================
# ANALYZE QUERY PERFORMANCE
# ============================================================

times = []

with open(INPUT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        times.append(float(row["time_ms"]))

print("========================================")
print("BLOCKCHAIN QUERY PERFORMANCE")
print("========================================")
print("Input file        :", INPUT)
print("Number of queries :", len(times))
print(f"Minimum time      : {min(times):.2f} ms")
print(f"Maximum time      : {max(times):.2f} ms")
print(f"Average time      : {statistics.mean(times):.2f} ms")
print(f"Median time       : {statistics.median(times):.2f} ms")
print(f"Std deviation     : {statistics.stdev(times):.2f} ms")