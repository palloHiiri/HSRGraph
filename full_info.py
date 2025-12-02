"""
сводка по персонажам и врагам.
"""
import argparse
from rdflib import Graph, Namespace, RDF, URIRef, Literal, RDFS

HSR = Namespace("http://example.org/hsr-ontology#")

def local_name(node):
    if isinstance(node, URIRef):
        s = str(node)
        if "#" in s:
            return s.split("#")[-1]
        return s.rstrip("/").split("/")[-1]
    if isinstance(node, Literal):
        return str(node)
    return str(node)

def gather_list(graph, subject, predicate):
    return [local_name(o) for o in graph.objects(subject, predicate)]

def gather_one(graph, subject, predicate):
    for o in graph.objects(subject, predicate):
        return local_name(o)
    return None

def summarize_character(graph, char_uri):
    summary = {}
    summary["character"] = local_name(char_uri)
    summary["recommendedLightCone"] = gather_one(graph, char_uri, HSR.recommendedLightCone)
    summary["alternativeLightCones"] = gather_list(graph, char_uri, HSR.hasAlternativeLightCones)
    summary["recommendedMainStatBody"] = gather_one(graph, char_uri, HSR.recommendedMainStatBody)
    summary["recommendedMainStatFeet"] = gather_one(graph, char_uri, HSR.recommendedMainStatFeet)
    summary["recommendedMainStatSphere"] = gather_one(graph, char_uri, HSR.recommendedMainStatSphere)
    summary["recommendedMainStatRope"] = gather_one(graph, char_uri, HSR.recommendedMainStatRope)
    summary["recommendedSubStats"] = gather_list(graph, char_uri, HSR.recommendedSubStats)

    cavern = gather_list(graph, char_uri, HSR.hasCavernRelic)
    planar = gather_list(graph, char_uri, HSR.hasPlanarRelic)

    if not cavern and not planar:
        fallback = gather_list(graph, char_uri, HSR.hasSet)

        if len(fallback) == 2:
            cavern = [fallback[0]]
            planar = [fallback[1]]
        elif len(fallback) == 1:
            cavern = [fallback[0]]

    summary["cavernRelics"] = cavern
    summary["planarRelics"] = planar

    summary["element"] = gather_one(graph, char_uri, HSR.hasElement)
    summary["path"] = gather_one(graph, char_uri, HSR.hasPath)
    return summary

def print_summary(summary):
    print("===============================================")
    print(f"Персонаж: {summary.get('character')}")
    if summary.get("element"):
        print(f"  Элемент: {summary.get('element')}")
    if summary.get("path"):
        print(f"  Путь: {summary.get('path')}")
    print(f"  Основной конус: {summary.get('recommendedLightCone') or '—'}")
    if summary.get("alternativeLightCones"):
        print(f"  Альтернативные конусы: {', '.join(summary.get('alternativeLightCones'))}")
    print("  Главные статы:")
    print(f"    Body:   {summary.get('recommendedMainStatBody') or '—'}")
    print(f"    Feet:   {summary.get('recommendedMainStatFeet') or '—'}")
    print(f"    Sphere: {summary.get('recommendedMainStatSphere') or '—'}")
    print(f"    Rope:   {summary.get('recommendedMainStatRope') or '—'}")
    if summary.get("recommendedSubStats"):
        print(f"  Побочные статы: {', '.join(summary.get('recommendedSubStats'))}")
    else:
        print("  Побочные статы: —")

    cav = summary.get("cavernRelics") or []
    plan = summary.get("planarRelics") or []
    if cav:
        print(f"  Пещерные реликвии: {', '.join(cav)}")
    else:
        print("  Пещерные реликвии: —")
    if plan:
        print(f"  Планарные реликвии: {', '.join(plan)}")
    else:
        print("  Планарные реликвии: —")
    print()

def summarize_enemy(graph, enemy_uri):
    summary = {}
    label = None
    for l in graph.objects(enemy_uri, RDFS.label):
        label = str(l)
        break
    summary["enemy"] = label if label else local_name(enemy_uri)
    summary["weaknesses"] = gather_list(graph, enemy_uri, HSR.hasWeakness)
    summary["elements"] = gather_list(graph, enemy_uri, HSR.hasElement)
    summary["source"] = gather_one(graph, enemy_uri, HSR.sourceURL)
    return summary

def print_enemy_summary(summary):
    print("===============================================")
    print(f"Враг: {summary.get('enemy')}")
    weaks = summary.get("weaknesses") or []
    if weaks:
        print(f"  Слабости (hasWeakness): {', '.join(weaks)}")
    else:
        print("  Слабости (hasWeakness): —")
    print()

def find_character_uri_by_name(graph, name):
    lname = name.strip().lower()
    for subj in graph.subjects(RDF.type, HSR.Character):
        if local_name(subj).lower() == lname:
            return subj
    for subj in graph.subjects(RDF.type, HSR.Character):
        if lname in str(subj).lower():
            return subj
    return None

def main():
    ap = argparse.ArgumentParser(description="HSR character and enemy summary from ontology")
    ap.add_argument("ontology", nargs="?", default="data/hsr_ontology.rdf",
                    help="Путь к RDF-файлу (xml/ttl) с онтологией; по умолчанию data/hsr_ontology.rdf")
    ap.add_argument("--char", "-c", help="Локальное имя персонажа (например 'Seele')")
    args = ap.parse_args()

    g = Graph()
    try:
        g.parse(args.ontology)
    except Exception as e:
        print("Ошибка при загрузке графа:", e)
        return

    # персонажи
    if args.char:
        uri = find_character_uri_by_name(g, args.char)
        if not uri:
            print(f"Персонаж '{args.char}' не найден.")
            return
        summary = summarize_character(g, uri)
        print_summary(summary)
    else:
        found = False
        for subj in sorted(set(g.subjects(RDF.type, HSR.Character)), key=lambda x: local_name(x)):
            found = True
            summary = summarize_character(g, subj)
            print_summary(summary)
        if not found:
            print("Не найдено ни одного hsr:Character в графе.")

    # враги и их слабости
    any_enemies = False
    for enemy in sorted(set(g.subjects(RDF.type, HSR.Enemies)), key=lambda x: local_name(x)):
        any_enemies = True
        esum = summarize_enemy(g, enemy)
        print_enemy_summary(esum)
    if not any_enemies:
        print("Не найдено ни одного hsr:Enemies в графе.")

if __name__ == "__main__":
    main()