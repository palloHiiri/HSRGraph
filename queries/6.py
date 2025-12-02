"""
Находит и выводит все команды, в которые входит заданный персонаж.
Для каждой команды выводится её название и список всех её членов с указанием их ролей.
"""
from rdflib import Graph, Namespace, RDFS, Literal, URIRef

HSR = Namespace("http://example.org/hsr-ontology#")
ONTOLOGY_PATH = "data/hsr_ontology.rdf"
CHARACTER = "Archer"  


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

    SELECT DISTINCT ?roleName ?member ?memberLabel WHERE {{
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
    }}
    ORDER BY ?roleName ?member
    """
    res = g.query(q)
    members = []
    for row in res:
        role = str(row.roleName) if hasattr(row, "roleName") and row.roleName is not None else "Member"
        member = row.member
        member_label = str(row.memberLabel) if hasattr(row, "memberLabel") and row.memberLabel is not None else None
        members.append((role, member, member_label))
    return members


def main():
    g = Graph()
    try:
        g.parse(ONTOLOGY_PATH, format="xml")
    except Exception as e:
        print("Failed to load ontology:", e)
        return

    char_uri = HSR[CHARACTER]

    q = f"""
    PREFIX hsr: <http://example.org/hsr-ontology#>

    SELECT DISTINCT ?team WHERE {{
      {{ ?team hsr:hasDPS <{char_uri}> . }}
      UNION {{ ?team hsr:hasSupport <{char_uri}> . }}
      UNION {{ ?team hsr:hasSustain <{char_uri}> . }}
      UNION {{ ?team hsr:hasMember <{char_uri}> . }}
      FILTER EXISTS {{ ?team a hsr:Team. }}
    }}
    ORDER BY ?team
    """
    try:
        res = g.query(q)
    except Exception as e:
        print("SPARQL query failed:", e)
        return

    teams = [row.team for row in res]
    if not teams:
        print(f"No teams found containing character {CHARACTER}.")
        return

    for team in teams:
        team_label = g.value(team, RDFS.label)
        team_name = str(team_label) if team_label else pretty_name(g, team)
        print(f"Team: {team_name}")
        members = get_team_members(g, team)
        if not members:
            print("Члены команды: —")
        else:
            print("Члены команды:")
            for role, member_uri, member_label in members:
                name = member_label if member_label else pretty_name(g, member_uri)
                print(f"  {role} - {name}")
        print()  

if __name__ == "__main__":
    main()