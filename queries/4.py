"""
Персонажи, покрывающие слабости Stormbringer и рекоммендуемые артефакты для них.
Выбирает отряд из четырех подходящих персонажей.
"""

from rdflib import Graph, Namespace, RDFS
import random

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

    q_support = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?weakElem ?path ?cavernRelic ?planarRelic
    WHERE {{
      <{boss_uri}> hsr:hasWeakness ?weakElem .
      ?character a hsr:Character .
      ?character hsr:hasElement ?weakElem .
      ?character hsr:hasPath ?path .
      FILTER (?path IN (hsr:Abundance, hsr:Preservation))
      OPTIONAL {{ ?character hsr:hasCavernRelic ?cavernRelic. }}
      OPTIONAL {{ ?character hsr:hasPlanarRelic ?planarRelic. }}
    }}
    """
    
    q_harmony = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?weakElem ?path ?cavernRelic ?planarRelic
    WHERE {{
      <{boss_uri}> hsr:hasWeakness ?weakElem .
      ?character a hsr:Character .
      ?character hsr:hasElement ?weakElem .
      ?character hsr:hasPath hsr:Harmony .
      OPTIONAL {{ ?character hsr:hasCavernRelic ?cavernRelic. }}
      OPTIONAL {{ ?character hsr:hasPlanarRelic ?planarRelic. }}
    }}
    """
    
    q_others = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    SELECT DISTINCT ?character ?weakElem ?path ?cavernRelic ?planarRelic
    WHERE {{
      <{boss_uri}> hsr:hasWeakness ?weakElem .
      ?character a hsr:Character .
      ?character hsr:hasElement ?weakElem .
      ?character hsr:hasPath ?path .
      OPTIONAL {{ ?character hsr:hasCavernRelic ?cavernRelic. }}
      OPTIONAL {{ ?character hsr:hasPlanarRelic ?planarRelic. }}
    }}
    """
    
    support_list = list(g.query(q_support))
    harmony_list = list(g.query(q_harmony))
    others_list = list(g.query(q_others))
    
    selected = []
    selected_uris = set()
    
    if support_list:
        choice = random.choice(support_list)
        selected.append(choice)
        selected_uris.add(choice.character)
    
    if harmony_list:
        available_harmony = [c for c in harmony_list if c.character not in selected_uris]
        if available_harmony:
            choice = random.choice(available_harmony)
            selected.append(choice)
            selected_uris.add(choice.character)
    
    available_others = [c for c in others_list if c.character not in selected_uris]
    random.shuffle(available_others)
    for char in available_others[:2]:
        selected.append(char)
        selected_uris.add(char.character)
    
    print("character_label |cavernRelic_label | planarRelic_label")
    print("-" * 140)
    for row in selected:
        char = row.character
        cavern = row.cavernRelic if hasattr(row, "cavernRelic") else None
        planar = row.planarRelic if hasattr(row, "planarRelic") else None
        print(
            f"{pretty_name(g, char)} | "
            f"{pretty_name(g, cavern) if cavern is not None else '-'} | "
            f"{pretty_name(g, planar) if planar is not None else '-'}"
        )


if __name__ == "__main__":
    main()