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

rules = sorted(
    set(g.subjects(RDF.type, SWRL.Imp)),
    key=lambda x: str(x)
)

def rdf_list_items(graph, head):
    items = []
    while head and head != RDF.nil:
        first = graph.value(head, RDF.first)
        if first is not None:
            items.append(first)
        head = graph.value(head, RDF.rest)
    return items

def short(value):
    if value is None:
        return "?"
    try:
        return g.namespace_manager.normalizeUri(value)
    except:
        return str(value)

def describe_atom(atom):
    atom_type = g.value(atom, RDF.type)

    if atom_type == SWRL.ClassAtom:
        cls = g.value(atom, SWRL.classPredicate)
        arg1 = g.value(atom, SWRL.argument1)
        return f"{short(cls)}({short(arg1)})"

    if atom_type == SWRL.IndividualPropertyAtom:
        prop = g.value(atom, SWRL.propertyPredicate)
        arg1 = g.value(atom, SWRL.argument1)
        arg2 = g.value(atom, SWRL.argument2)
        return f"{short(prop)}({short(arg1)}, {short(arg2)})"

    if atom_type == SWRL.DatavaluedPropertyAtom:
        prop = g.value(atom, SWRL.propertyPredicate)
        arg1 = g.value(atom, SWRL.argument1)
        arg2 = g.value(atom, SWRL.argument2)
        return f"{short(prop)}({short(arg1)}, {short(arg2)})"

    return f"UnknownAtom({short(atom)})"

print("=" * 70)
print("SWRL RULE DETAILS")
print("=" * 70)
print("Total SWRL rules:", len(rules))

for i, rule in enumerate(rules, 1):
    body_head = g.value(rule, SWRL.body)
    head_head = g.value(rule, SWRL.head)

    body = [describe_atom(x) for x in rdf_list_items(g, body_head)]
    head = [describe_atom(x) for x in rdf_list_items(g, head_head)]

    print(f"\nRULE {i}")
    print("IF  :", " ^ ".join(body))
    print("THEN:", " ^ ".join(head))