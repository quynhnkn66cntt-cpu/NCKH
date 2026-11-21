from rdflib import Graph, RDF, Namespace
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR.parent / "config.yaml"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

BASE_DIR = (SCRIPT_DIR.parent / config["project"]["root_dir"]).resolve()

ONTOLOGY = BASE_DIR / config["paths"]["ontology_blockchain"]

SWRL = Namespace("http://www.w3.org/2003/11/swrl#")
g = Graph()
g.parse(ONTOLOGY)

rules = list(g.subjects(RDF.type, SWRL.Imp))

def list_items(head):
    result = []
    while head and head != RDF.nil:
        item = g.value(head, RDF.first)
        if item:
            result.append(item)
        head = g.value(head, RDF.rest)
    return result

for i, rule in enumerate(rules, 1):
    variables = set()

    for part in [SWRL.body, SWRL.head]:
        head = g.value(rule, part)

        for atom in list_items(head):
            for arg_property in [SWRL.argument1, SWRL.argument2]:
                arg = g.value(atom, arg_property)

                if arg is not None and (arg, RDF.type, SWRL.Variable) in g:
                    variables.add(str(arg))

    print(f"\nRULE {i}")

    for v in sorted(variables):
        if "#" in v:
            print("  HASH VARIABLE :", v)
        else:
            print("  SLASH VARIABLE:", v)
