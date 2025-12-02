"""
Подбор сетов, которые используют персонажи пути Preservation, против босса Cocolia, Mother of Deception,
"""
from rdflib import Graph, Namespace, RDFS

HSR = Namespace("http://example.org/hsr-ontology#")
ONTOLOGY_PATH = "data/hsr_ontology.rdf"
PATH = "Preservation"
BOSS = "Cocolia,_Mother_of_Deception"  


def pretty_name(g: Graph, node):
    if node is None:
        return "-"
    lbl = g.value(node, RDFS.label)
    if lbl:
        return str(lbl)
    s = str(node)
    return s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]


def main():
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="xml")

    path_uri = HSR[PATH]
    boss_uri = HSR[BOSS]

    boss_weak = [pretty_name(g, w) for w in g.objects(boss_uri, HSR.hasWeakness)]
    if boss_weak:
        print(f"Boss {BOSS} weaknesses: {', '.join(boss_weak)}")
    else:
        print(f"No weaknesses recorded for boss {BOSS} (or boss not found).")

    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?char ?set
    WHERE {{
      ?char a hsr:Character .
      ?char hsr:hasPath <{path_uri}> .
      {{ ?char hsr:hasCavernRelic ?set . }} UNION {{ ?char hsr:hasPlanarRelic ?set . }}
    }}
    ORDER BY ?set
    """
    res = g.query(q)
    print("char_label | relics_label")
    print("-" * 100)
    for row in res:
        char = row.char
        set_ = row.set
        print(f"{pretty_name(g, char)}| {pretty_name(g, set_)}")


if __name__ == "__main__":
    main()