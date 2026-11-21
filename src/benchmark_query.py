
import csv
import time
from pathlib import Path

from verify_live import get_live_event

# 2 events per type, 7 types
EVENTS = [
    ("EV112", "DISTRIBUTION", "DL001"),
    ("EV116", "DISTRIBUTION", "DL005"),
    ("EV006", "FEEDING", "FB001"),
    ("EV080", "FEEDING", "FB075"),
    ("EV097", "HARVEST", "H001"),
    ("EV101", "HARVEST", "H005"),
    ("EV102", "PROCESSING", "PR001"),
    ("EV106", "PROCESSING", "PR005"),
    ("EV001", "SEED_STOCKING", "LOT001"),
    ("EV005", "SEED_STOCKING", "LOT005"),
    ("EV107", "SHIPPING", "S001"),
    ("EV111", "SHIPPING", "S005"),
    ("EV081", "TREATMENT", "TR001"),
    ("EV096", "TREATMENT", "TR016"),
]

REPEATS = 3

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = (
    BASE_DIR
    / "04_blockchain"
    / "results"
    / "query_performance_extended.csv"
)


def main():
    # Prevent accidental overwriting of previous measurements
    if OUTPUT.exists():
        raise FileExistsError(
            f"Output already exists: {OUTPUT}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    results = []
    run = 0

    for repeat in range(1, REPEATS + 1):
        for event_id, event_type, batch_id in EVENTS:
            run += 1
            status = "SUCCESS"
            error = ""

            start = time.perf_counter()

            try:
                result = get_live_event(event_id)

                if (
                    result.get("eventID") != event_id
                    or result.get("eventType") != event_type
                    or result.get("batchID") != batch_id
                ):
                    raise ValueError(
                        "Blockchain event fields do not match"
                    )

            except Exception as exc:
                status = "FAILED"
                error = str(exc).replace("\n", " ")[:300]

            elapsed_ms = (
                time.perf_counter() - start
            ) * 1000

            results.append({
                "run": run,
                "repeat": repeat,
                "eventID": event_id,
                "eventType": event_type,
                "batchID": batch_id,
                "time_ms": round(elapsed_ms, 3),
                "status": status,
                "error": error,
            })

            print(
                f"[{run:02d}/42] "
                f"{event_id} "
                f"{event_type} "
                f"{elapsed_ms:.2f} ms "
                f"{status}",
                flush=True,
            )

    with open(
        OUTPUT, "x", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=results[0].keys()
        )
        writer.writeheader()
        writer.writerows(results)

    successful = sum(
        row["status"] == "SUCCESS"
        for row in results
    )

    print("\n========== BENCHMARK SUMMARY ==========")
    print("Total queries :", len(results))
    print("Successful    :", successful)
    print("Failed        :", len(results) - successful)
    print("Output        :", OUTPUT)


if __name__ == "__main__":
    main()
