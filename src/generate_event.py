from pathlib import Path
import pandas as pd
import json
import yaml

# ==========================================
# 1. LOAD CONFIGURATION
# ==========================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
DATA_DIR = BASE_DIR / config["paths"]["source_csv"]

OUTPUT_DIR = BASE_DIR / config["paths"]["payloads"]
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# ==========================================
# 2. HÀM CHUYỂN NGÀY SANG ISO
# ==========================================

def to_iso_datetime(value):
    """
    Giữ nguyên ngày và giờ từ CSV.
    Dùng cho FEEDING, TREATMENT, HARVEST,
    PROCESSING, SHIPPING, DISTRIBUTION.
    """
    if pd.isna(value):
        return None

    dt = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(dt):
        return None

    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def to_iso_date_at_8am(value):
    """
    SEED_STOCKING trong seed_lots.csv chỉ có ngày,
    nên quy ước thời gian nhập giống là 08:00:00.
    """
    if pd.isna(value):
        return None

    dt = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(dt):
        return None

    return dt.strftime("%Y-%m-%d") + "T08:00:00"

# ==========================================
# 3. ĐỌC CÁC FILE CSV
# ==========================================

farms_ponds = pd.read_csv(
    DATA_DIR / "farms_ponds.csv",
    encoding="utf-8"
).dropna(how="all")

seed_lots = pd.read_csv(
    DATA_DIR / "seed_lots.csv",
    encoding="utf-8"
).dropna(how="all")

feed_batches = pd.read_csv(
    DATA_DIR / "feed_batches.csv",
    encoding="utf-8"
).dropna(how="all")

treatments = pd.read_csv(
    DATA_DIR / "treatment_records.csv",
    encoding="utf-8"
).dropna(how="all")

harvest_lots = pd.read_csv(
    DATA_DIR / "harvest_lots.csv",
    encoding="utf-8"
).dropna(how="all")

processing_lots = pd.read_csv(
    DATA_DIR / "processing_lots.csv",
    encoding="utf-8"
).dropna(how="all")

shipments = pd.read_csv(
    DATA_DIR / "shipments.csv",
    encoding="utf-8"
).dropna(how="all")

distribution_lots = pd.read_csv(
    DATA_DIR / "distribution_lots.csv",
    encoding="utf-8"
).dropna(how="all")


# ==========================================
# 4. BIẾN ĐẾM EVENT
# ==========================================

event_number = 1
event_count = 0
event_id = 0

def save_event(event):
    global event_number
    global event_count

    event_id = f"EV{event_number:03d}"
    event["eventID"] = event_id

    output_file = OUTPUT_DIR / f"{event_id}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            event,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(f"Da tao {event_id}: {event['eventType']}")

    event_number += 1
    event_count += 1


# ==========================================
# 5. SEED STOCKING
# ==========================================

for _, row in seed_lots.iterrows():

    seed_lot_id = str(row["seed_lot_id"]).strip()
    pond_id = str(row["pond_id"]).strip()

    pond = farms_ponds[
        farms_ponds["pond_id"].astype(str).str.strip() == pond_id
    ]

    if len(pond) == 0:
        print(f"BO QUA {seed_lot_id}: khong tim thay {pond_id}")
        continue

    pond = pond.iloc[0]

    farm_id = str(pond["farm_id"]).strip()
    farm_name = str(
    farms_ponds.loc[
        farms_ponds["pond_id"].astype(str).str.strip() == pond_id,
        "farm_name"
    ].iloc[0]
).strip()
    event = {
    "eventID": event_id,
    "batchID": seed_lot_id,
    "eventType": "SEED_STOCKING",
    "actorID": farm_id,
    "timestamp": to_iso_date_at_8am(row["stocking_date"]),
    "data": {
        "seedLotID": seed_lot_id,
        "speciesCode": str(row["species_code"]).strip(),
        "supplier": str(row["supplier"]).strip(),
        "pondID": pond_id,
        "farmID": farm_id,
        "farmName": farm_name,
        "quantity": int(row["quantity"])
    }
}

    save_event(event)


# ==========================================
# 6. FEEDING
# ==========================================

for _, row in feed_batches.iterrows():

    feed_id = str(row["feed_batch_id"]).strip()
    pond_id = str(row["pond_id"]).strip()

    pond = farms_ponds[
        farms_ponds["pond_id"].astype(str).str.strip() == pond_id
    ]

    if len(pond) == 0:
        print(f"BO QUA {feed_id}: khong tim thay {pond_id}")
        continue

    pond = pond.iloc[0]
    farm_id = str(pond["farm_id"]).strip()

    event = {
        "eventID": "",
        "batchID": feed_id,
        "eventType": "FEEDING",
        "actorID": farm_id,
        "timestamp": to_iso_datetime(row["date_used"]),
        "data": {
            "feedBatchID": feed_id,
            "brand": str(row["brand"]).strip(),
            "feedType": str(row["feed_type"]).strip(),
            "pondID": pond_id,
            "farmID": farm_id,
            "quantity": float(row["quantity"])
        }
    }

    save_event(event)


# ==========================================
# 7. TREATMENT
# ==========================================

for _, row in treatments.iterrows():

    treatment_id = str(row["treatment_id"]).strip()
    pond_id = str(row["pond_id"]).strip()

    pond = farms_ponds[
        farms_ponds["pond_id"].astype(str).str.strip() == pond_id
    ]

    if len(pond) == 0:
        print(f"BO QUA {treatment_id}: khong tim thay {pond_id}")
        continue

    pond = pond.iloc[0]
    farm_id = str(pond["farm_id"]).strip()

    event = {
        "eventID": "",
        "batchID": treatment_id,
        "eventType": "TREATMENT",
        "actorID": farm_id,
        "timestamp": to_iso_datetime(row["date_used"]),
        "data": {
            "treatmentID": treatment_id,
            "productName": str(row["product_name"]).strip(),
            "purpose": str(row["purpose"]).strip(),
            "pondID": pond_id,
            "farmID": farm_id,
            "dosage": str(row["dosage"]).strip()
        }
    }

    save_event(event)


# ==========================================
# 8. HARVEST
# ==========================================

for _, row in harvest_lots.iterrows():

    harvest_id = str(row["harvest_lot_id"]).strip()
    pond_id = str(row["pond_id"]).strip()

    pond = farms_ponds[
        farms_ponds["pond_id"].astype(str).str.strip() == pond_id
    ]

    if len(pond) == 0:
        print(f"BO QUA {harvest_id}: khong tim thay {pond_id}")
        continue

    pond = pond.iloc[0]
    farm_id = str(pond["farm_id"]).strip()

    event = {
        "eventID": "",
        "batchID": harvest_id,
        "eventType": "HARVEST",
        "actorID": farm_id,
        "timestamp": to_iso_datetime(row["harvest_date"]),
        "data": {
            "harvestLotID": harvest_id,
            "pondID": pond_id,
            "farmID": farm_id,
            "quantityKg": float(row["quantity_kg"]),
            "qualityNote": str(row["quality_note"]).strip()
        }
    }

    save_event(event)


# ==========================================
# 9. PROCESSING
# ==========================================

for _, row in processing_lots.iterrows():

    processing_id = str(row["processing_lot_id"]).strip()
    harvest_id = str(row["harvest_lot_id"]).strip()
    plant_id = str(row["plant_id"]).strip()

    event = {
        "eventID": "",
        "batchID": processing_id,
        "eventType": "PROCESSING",
        "actorID": plant_id,
        "timestamp": to_iso_datetime(row["process_date"]),
        "data": {
            "processingLotID": processing_id,
            "harvestLotID": harvest_id,
            "plantID": plant_id,
            "output_Qty": float(row["output_quantity"])
        }
    }

    save_event(event)


# ==========================================
# 10. SHIPPING
# ==========================================

for _, row in shipments.iterrows():

    shipment_id = str(row["shipment_id"]).strip()
    processing_id = str(row["processing_lot_id"]).strip()
    transporter_id = str(row["transporter_id"]).strip()

    event = {
        "eventID": "",
        "batchID": shipment_id,
        "eventType": "SHIPPING",
        "actorID": transporter_id,
        "timestamp": to_iso_datetime(row["shipment_date"]),
        "data": {
            "shipmentID": shipment_id,
            "processingLotID": processing_id,
            "transporterID": transporter_id,
            "destination": str(row["destination"]).strip()
        }
    }

    save_event(event)


# ==========================================
# 11. DISTRIBUTION
# ==========================================

for _, row in distribution_lots.iterrows():

    distribution_lot_id = str(row["distribution_lot_id"]).strip()

    event_id += 1

    event = {
        "eventID": f"EV{event_id:03d}",
        "batchID": distribution_lot_id,
        "eventType": "DISTRIBUTION",
        "actorID": str(row["receiver_id"]).strip(),
        "timestamp": to_iso_datetime(row["receive_date"]),
        
        "data": {
            "distributionLotID": distribution_lot_id,
            "shipmentID": str(row["shipment_id"]).strip(),
            "receiverID": str(row["receiver_id"]).strip(),
            "market": str(row["market"]).strip()
        }
    }
    
    save_event(event)


# ==========================================
# 12. KẾT QUẢ
# ==========================================

print("\n==========================================")
print("HOAN THANH SINH TRACEABILITY EVENTS")
print("==========================================")

print(f"Tong so event: {event_count}")
print(f"Thu muc output: {OUTPUT_DIR}")