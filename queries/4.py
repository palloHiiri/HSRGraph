"""
Персонажи, покрывающие слабости Stormbringer.
"""

from rdflib import Graph, Namespace, RDFS

HSR = Namespace("http://example.org/hsr-ontology#")
ONTOLOGY_PATH = "data/hsr_ontology.rdf"
BOSS = "Stormbringer"


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

    boss_uri = HSR[BOSS]

    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?weakElem ?recommendedLC
    WHERE {{
      <{boss_uri}> hsr:hasWeakness ?weakElem .
      ?character a hsr:Character .
      ?character hsr:hasElement ?weakElem .
      OPTIONAL {{ ?character hsr:recommendedLightCone ?recommendedLC. }}
    }}
    ORDER BY ?character
    """
    res = g.query(q)
    print("character_label | weakness_label |recommendedLC_label")
    print("-" * 140)
    for row in res:
        char = row.character
        weak = row.weakElem
        lc = row.recommendedLC if hasattr(row, "recommendedLC") else None
        print(
            f"{pretty_name(g, char)} | "
            f"{pretty_name(g, weak)} | "
            f"{pretty_name(g, lc) if lc is not None else '-'}"
        )


if __name__ == "__main__":
    main()