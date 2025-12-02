"""
Подбор возможных персонажей против Doomsday Beast при условии уязвимости к элементу Wind, а также рекомендуемые световые конусы.
Возвращает до 4 персонажей с элементом Wind, один из которых следует пути Abundance или Preservation.
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

    q_support = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?path ?recommendedLC
    WHERE {{
      ?character a hsr:Character .
      ?character hsr:hasElement <{elem_uri}> .
      ?character hsr:hasPath ?path .
      FILTER (?path IN (hsr:Abundance, hsr:Preservation))
      OPTIONAL {{ ?character hsr:recommendedLightCone ?recommendedLC. }}
    }}
    ORDER BY ?character
    LIMIT 1
    """

    q_others = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?path ?recommendedLC
    WHERE {{
      ?character a hsr:Character .
      ?character hsr:hasElement <{elem_uri}> .
      ?character hsr:hasPath ?path .
      FILTER (?path NOT IN (hsr:Abundance, hsr:Preservation))
      OPTIONAL {{ ?character hsr:recommendedLightCone ?recommendedLC. }}
    }}
    ORDER BY ?character
    LIMIT 3
    """
    
    print("character_label | path_label | recommendedLC_label")
    print("-" * 100)
    
    # Get support character
    res_support = g.query(q_support)
    for row in res_support:
        char = row.character
        path = row.path if hasattr(row, "path") else None
        lc = row.recommendedLC if hasattr(row, "recommendedLC") else None
        print(f"{pretty_name(g, char)} | {pretty_name(g, path) if path else '-'} | {pretty_name(g, lc) if lc is not None else '-'}")
    
    # Get other characters
    res_others = g.query(q_others)
    for row in res_others:
        char = row.character
        path = row.path if hasattr(row, "path") else None
        lc = row.recommendedLC if hasattr(row, "recommendedLC") else None
        print(f"{pretty_name(g, char)} | {pretty_name(g, path) if path else '-'} | {pretty_name(g, lc) if lc is not None else '-'}")


if __name__ == "__main__":
    main()