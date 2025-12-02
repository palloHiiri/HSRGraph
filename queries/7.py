"""
Команды, покрывающие слабости босса, с фильтром по количеству совпадений.

Выводит только те команды, в которых 3 или 4 участника имеют элемент,
совпадающий с уязвимостями босса.
"""
from collections import defaultdict
from rdflib import Graph, Namespace, RDFS, Literal, URIRef

HSR = Namespace("http://example.org/hsr-ontology#")
ONTOLOGY_PATH = "data/hsr_ontology.rdf"
BOSS = "Phantylia_the_Undying"


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


def get_team_members(g: Graph, team_uri: URIRef):
    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?roleName ?member ?memberLabel ?element WHERE {{
      {{
        <{team_uri}> hsr:hasDPS ?member .
        BIND("DPS" AS ?roleName)
      }} UNION {{
        <{team_uri}> hsr:hasSupport ?member .
        BIND("Support" AS ?roleName)
      }} UNION {{
        <{team_uri}> hsr:hasSustain ?member .
        BIND("Sustain" AS ?roleName)
      }} UNION {{
        <{team_uri}> hsr:hasMember ?member .
        BIND("Member" AS ?roleName)
      }}
      OPTIONAL {{ ?member rdfs:label ?memberLabel. }}
      OPTIONAL {{ ?member hsr:hasElement ?element. }}
    }}
    ORDER BY ?roleName ?member
    """
    res = g.query(q)
    members = []
    for row in res:
        role = str(row.roleName) if hasattr(row, "roleName") and row.roleName is not None else "Member"
        member = row.member
        member_label = str(row.memberLabel) if hasattr(row, "memberLabel") and row.memberLabel is not None else None
        element = row.element if hasattr(row, "element") else None
        members.append((role, member, member_label, element))
    return members


def main():
    g = Graph()
    try:
        g.parse(ONTOLOGY_PATH, format="xml")
    except Exception as e:
        print("Failed to load ontology:", e)
        return

    boss_uri = HSR[BOSS]
    boss_weaknesses = set(g.objects(boss_uri, HSR.hasWeakness))
    if not boss_weaknesses:
        print(f"Warning: boss {BOSS} has no recorded hsr:hasWeakness in the ontology.")
    else:
        print("Boss weaknesses:", ", ".join(pretty_name(g, w) for w in boss_weaknesses))
    print()

    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?team ?teamLabel WHERE {{
      ?team a hsr:Team .
      OPTIONAL {{ ?team rdfs:label ?teamLabel. }}
    }}
    ORDER BY ?team
    """
    try:
        teams_res = g.query(q)
    except Exception as e:
        print("SPARQL query failed:", e)
        return

    teams = [row.team for row in teams_res]

    results = []
    for team in teams:
        members = get_team_members(g, team)
        matches = []
        for role, member_uri, member_label, element in members:
            if element and element in boss_weaknesses:
                matches.append((role, member_uri, member_label))
        if len(matches) in (3, 4):
            results.append((team, members, matches))

    results.sort(key=lambda x: (-len(x[2]), pretty_name(g, x[0])))

    if not results:
        print("No teams found that cover the boss weaknesses with exactly 3 or 4 matching members.")
        return

    for team, members, matches in results:
        team_label = g.value(team, RDFS.label)
        team_name = str(team_label) if team_label else pretty_name(g, team)
        print(f"Team: {team_name}")

        if not members:
            print("Члены команды: —")
        else:
            print("Члены команды:")
            for role, member_uri, member_label, element in members:
                name = member_label if member_label else pretty_name(g, member_uri)
                print(f"  {role} - {name}")

        match_count = len(matches)
        matching_names = ", ".join(m[2] if m[2] else pretty_name(g, m[1]) for m in sorted(matches, key=lambda x: pretty_name(g, x[1])))
        print(f"Matches: {match_count} — matching members: {matching_names}")
        print()  


if __name__ == "__main__":
    main()