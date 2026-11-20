from pathlib import Path
import pandas as pd
import yaml
# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN
# ==========================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
DATA_DIR = BASE_DIR / config["paths"]["source_csv"]
# Danh sách các file dữ liệu
files = [
    "actors.csv",
    "farms_ponds.csv",
    "seed_lots.csv",
    "feed_batches.csv",
    "treatment_records.csv",
    "harvest_lots.csv",
    "processing_lots.csv",
    "shipments.csv",
    "distribution_lots.csv",

]

data = {}

for file in files:

    path = DATA_DIR / file

    print("Dang doc:", path)

    df = pd.read_csv(path, encoding="utf-8")
    # Xóa các dòng hoàn toàn trống
    df = df.dropna(how="all")
    #df = pd.read_csv(path, encoding="cp1258")
    data[file] = df

    print("\n==========================")
    print(file)
    print("==========================")
    print("Cac cot:", list(df.columns))
    print("So dong:", len(df))
    print(df.head())
        # Kiểm tra dữ liệu trùng
    duplicate_count = df.duplicated().sum()
    print("So dong trung:", duplicate_count)

    # Kiểm tra ô trống
    missing_count = df.isnull().sum()
    print("So o trong:")
    print(missing_count)

    # Kiểm tra khoảng trắng ở đầu/cuối
    for col in df.select_dtypes(include="str").columns:
        space_count = df[col].astype(str).str.strip().ne(df[col].astype(str)).sum()
        if space_count > 0:
            print(f"Cot {col} co {space_count} gia tri co khoang trang thua")
    # ==========================================
# KIỂM TRA KHÓA NGOẠI GIỮA CÁC FILE
# ==========================================

print("\n\n==========================================")
print("KIEM TRA KHOA NGOAI")
print("==========================================")

# 1. processing_lots.harvest_lot_id
# phải tồn tại trong harvest_lots.harvest_lot_id
harvest_ids = set(data["harvest_lots.csv"]["harvest_lot_id"])

invalid_processing = data["processing_lots.csv"][
    ~data["processing_lots.csv"]["harvest_lot_id"].isin(harvest_ids)
]

print("\n[1] processing_lots -> harvest_lots")
if len(invalid_processing) == 0:
    print("OK - Tat ca harvest_lot_id deu ton tai")
else:
    print("LOI - Co harvest_lot_id khong ton tai:")
    print(invalid_processing)


# 2. shipments.processing_lot_id
# phải tồn tại trong processing_lots.processing_lot_id
processing_ids = set(data["processing_lots.csv"]["processing_lot_id"])

invalid_shipments = data["shipments.csv"][
    ~data["shipments.csv"]["processing_lot_id"].isin(processing_ids)
]

print("\n[2] shipments -> processing_lots")
if len(invalid_shipments) == 0:
    print("OK - Tat ca processing_lot_id deu ton tai")
else:
    print("LOI - Co processing_lot_id khong ton tai:")
    print(invalid_shipments)


# 3. distribution_lots.shipment_id
# phải tồn tại trong shipments.shipment_id
shipment_ids = set(data["shipments.csv"]["shipment_id"])

invalid_distribution = data["distribution_lots.csv"][
    ~data["distribution_lots.csv"]["shipment_id"].isin(shipment_ids)
]

print("\n[3] distribution_lots -> shipments")
if len(invalid_distribution) == 0:
    print("OK - Tat ca shipment_id deu ton tai")
else:
    print("LOI - Co shipment_id khong ton tai:")
    print(invalid_distribution)


# 4. seed_lots.pond_id
# phải tồn tại trong farms_ponds.csv
pond_ids = set(data["farms_ponds.csv"]["pond_id"])

invalid_seed = data["seed_lots.csv"][
    ~data["seed_lots.csv"]["pond_id"].isin(pond_ids)
]

print("\n[4] seed_lots -> farms_ponds")
if len(invalid_seed) == 0:
    print("OK - Tat ca pond_id cua seed_lots deu ton tai")
else:
    print("LOI - Co pond_id khong ton tai:")
    print(invalid_seed)


# 5. feed_batches.pond_id
invalid_feed = data["feed_batches.csv"][
    ~data["feed_batches.csv"]["pond_id"].isin(pond_ids)
]

print("\n[5] feed_batches -> farms_ponds")
if len(invalid_feed) == 0:
    print("OK - Tat ca pond_id cua feed_batches deu ton tai")
else:
    print("LOI - Co pond_id khong ton tai:")
    print(invalid_feed)


# 6. treatment_records.pond_id
invalid_treatment = data["treatment_records.csv"][
    ~data["treatment_records.csv"]["pond_id"].isin(pond_ids)
]

print("\n[6] treatment_records -> farms_ponds")
if len(invalid_treatment) == 0:
    print("OK - Tat ca pond_id cua treatment_records deu ton tai")
else:
    print("LOI - Co pond_id khong ton tai:")
    print(invalid_treatment)


# 7. harvest_lots.pond_id
invalid_harvest = data["harvest_lots.csv"][
    ~data["harvest_lots.csv"]["pond_id"].isin(pond_ids)
]

print("\n[7] harvest_lots -> farms_ponds")
if len(invalid_harvest) == 0:
    print("OK - Tat ca pond_id cua harvest_lots deu ton tai")
else:
    print("LOI - Co pond_id khong ton tai:")
    print(invalid_harvest)
# 8. processing_lots.plant_id
# phải tồn tại trong actors.actor_id
actor_ids = set(data["actors.csv"]["actor_id"])

invalid_processing_actor = data["processing_lots.csv"][
    ~data["processing_lots.csv"]["plant_id"].isin(actor_ids)
]

print("\n[8] processing_lots -> actors")
if len(invalid_processing_actor) == 0:
    print("OK - Tat ca plant_id deu ton tai trong actors")
else:
    print("LOI - Co plant_id khong ton tai:")
    print(invalid_processing_actor)


# 9. shipments.transporter_id
# phải tồn tại trong actors.actor_id
invalid_transporter = data["shipments.csv"][
    ~data["shipments.csv"]["transporter_id"].isin(actor_ids)
]

print("\n[9] shipments -> actors")
if len(invalid_transporter) == 0:
    print("OK - Tat ca transporter_id deu ton tai trong actors")
else:
    print("LOI - Co transporter_id khong ton tai:")
    print(invalid_transporter)


# 10. distribution_lots.receiver_id
# phải tồn tại trong actors.actor_id
invalid_receiver = data["distribution_lots.csv"][
    ~data["distribution_lots.csv"]["receiver_id"].isin(actor_ids)
]

print("\n[10] distribution_lots -> actors")
if len(invalid_receiver) == 0:
    print("OK - Tat ca receiver_id deu ton tai trong actors")
else:
    print("LOI - Co receiver_id khong ton tai:")
    print(invalid_receiver)
# ==========================================
# KIEM TRA VA CHUAN HOA ID
# ==========================================

print("\n\n==========================================")
print("KIEM TRA ID")
print("==========================================")

# Các cột ID cần kiểm tra
id_columns = {
    "actors.csv": ["actor_id"],
    "farms_ponds.csv": ["farm_id", "pond_id"],
    "seed_lots.csv": ["seed_lot_id"],
    "feed_batches.csv": ["feed_batch_id"],
    "treatment_records.csv": ["treatment_id"],
    "harvest_lots.csv": ["harvest_lot_id"],
    "processing_lots.csv": ["processing_lot_id"],
    "shipments.csv": ["shipment_id"],
    "distribution_lots.csv": ["distribution_lot_id"]
}

for file, columns in id_columns.items():

    print(f"\n--- {file} ---")

    df = data[file]

    for col in columns:

        # Lấy các ID
        ids = df[col].dropna().astype(str).str.strip()

        # Kiểm tra ID trùng
        duplicate_count = ids.duplicated().sum()

        # Kiểm tra ID rỗng
        empty_count = (ids == "").sum()

        print(f"\nCot: {col}")
        print(f"  So ID: {len(ids)}")
        print(f"  ID trung: {duplicate_count}")
        print(f"  ID rong: {empty_count}")

        # Hiển thị các ID
        print(f"  Danh sach ID: {ids.tolist()}")
    # ==========================================
# 8.4 - KIEM TRA MA LOAI TOM
# ==========================================

print("\n\n==========================================")
print("KIEM TRA SPECIES CODE")
print("==========================================")

# Lấy species_code từ farms_ponds
species_farm_pond = (
    data["farms_ponds.csv"]["species_code"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

print("\nSpecies code trong farms_ponds.csv:")
print(species_farm_pond)


# Lấy species_code từ seed_lots
species_seed = (
    data["seed_lots.csv"]["species_code"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

print("\nSpecies code trong seed_lots.csv:")
print(species_seed)


# Gộp tất cả mã loài
all_species = sorted(set(species_farm_pond) | set(species_seed))

print("\nTat ca species_code:")
print(all_species)