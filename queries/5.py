"""
Подбор сетов и конусов для пути Abundance
при иммунитете босса к Physical (по умолчанию без конкретного босса).
"""
from rdflib import Graph, Namespace, RDFS

HSR = Namespace("http://example.org/hsr-ontology#")
ONTOLOGY_PATH = "data/hsr_ontology.rdf"
PATH = "Abundance"
PHYSICAL = "Physical"


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
    physical_uri = HSR[PHYSICAL]

    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?element ?recommendedLC ?cavern ?planar
    WHERE {{
      ?character a hsr:Character .
      ?character hsr:hasPath <{path_uri}> .
      ?character hsr:hasElement ?element .
      FILTER (?element != <{physical_uri}>)
      OPTIONAL {{ ?character hsr:recommendedLightCone ?recommendedLC. }}
      OPTIONAL {{ ?character hsr:hasCavernRelic ?cavern. }}
      OPTIONAL {{ ?character hsr:hasPlanarRelic ?planar. }}
    }}
    ORDER BY ?character
    """
    res = g.query(q)
    print("character_label | element_label | recommendedLC_label | cavern_label | planar_label")
    print("-" * 100)
    for row in res:
        char = row.character
        element = row.element
        lc = row.recommendedLC if hasattr(row, "recommendedLC") else None
        cavern = row.cavern if hasattr(row, "cavern") else None
        planar = row.planar if hasattr(row, "planar") else None
        print(
            f"{pretty_name(g, char)} | "
            f"{pretty_name(g, element)} | "
            f"{pretty_name(g, lc) if lc is not None else '-'} | "
            f"{pretty_name(g, cavern) if cavern is not None else '-'} | "
            f"{pretty_name(g, planar) if planar is not None else '-'}"
        )


if __name__ == "__main__":
    main()