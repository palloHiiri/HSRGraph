"""
Подбор минимального состава отряда против Doomsday Beast при условии уязвимости к элементу Wind.
Возвращает до 4 персонажей с элементом Wind.
"""
from rdflib import Graph, Namespace, RDFS, Literal

HSR = Namespace("http://example.org/hsr-ontology#")
ONTOLOGY_PATH = "data/hsr_ontology.rdf"
BOSS = "Doomsday_Beast"
ELEMENT = "Wind"
LIMIT = 4


def pretty_name(g: Graph, node):
    if node is None:
        return "-"
    if isinstance(node, Literal):
        return str(node)
    lbl = g.value(node, RDFS.label)
    if lbl:
        return str(lbl)
    s = str(node)
    return s.split("#")[-1] if "#" in s else s.rstrip("/").split("/")[-1]


def main():
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="xml")

    boss_uri = HSR[BOSS]
    elem_uri = HSR[ELEMENT]

    boss_weaknesses = set(g.objects(boss_uri, HSR.hasWeakness))
    if elem_uri not in boss_weaknesses:
        print(f"Warning: boss {BOSS} does not list {ELEMENT} as a weakness in the ontology (found: {', '.join(pretty_name(g,x) for x in boss_weaknesses) or 'none'}).")

    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?recommendedLC
    WHERE {{
      ?character a hsr:Character .
      ?character hsr:hasElement <{elem_uri}> .
      OPTIONAL {{ ?character hsr:recommendedLightCone ?recommendedLC. }}
    }}
    ORDER BY ?character
    LIMIT {LIMIT}
    """
    res = g.query(q)
    print("character_label | recommendedLC_label")
    print("-" * 100)
    for row in res:
        char = row.character
        lc = row.recommendedLC if hasattr(row, "recommendedLC") else None
        print(f"{pretty_name(g, char)} | {pretty_name(g, lc) if lc is not None else '-'}")


if __name__ == "__main__":
    main()