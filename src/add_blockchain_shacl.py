from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config["project"]["root_dir"])
path = BASE_DIR / config["paths"]["shacl_shapes"]
text = path.read_text(encoding="utf-8")

old = '''    sh:property [
        sh:path :currentHash ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "TraceabilityEvent must have exactly one currentHash." ;
    ] .'''

new = '''    sh:property [
        sh:path :currentHash ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "TraceabilityEvent must have exactly one currentHash." ;
    ] ;

    sh:property [
        sh:path :txHash ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "TraceabilityEvent must have exactly one blockchain transaction ID (txHash)." ;
    ] ;

    sh:property [
        sh:path :blockNumber ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:long ;
        sh:message "TraceabilityEvent must have exactly one blockchain blockNumber." ;
    ] .'''

if old not in text:
    raise RuntimeError(
        "Khong tim thay currentHash block. File SHACL khong bi thay doi."
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Blockchain SHACL constraints added successfully.")
print("Saved:", path)