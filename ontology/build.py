from rdflib import Graph, Namespace, RDF, RDFS, OWL

HSR = Namespace("http://example.org/hsr-ontology#")

def normalize(term):
    return term.replace("The ", "").replace(" ", "_")

def build_ontology(path):
    g = Graph()
    g.bind("hsr", HSR)

    base_classes = ["Character", "Enemies", "LightCone", "Path", "Element", "Set", "Characteristic", "Team"]
    for cls_name in base_classes:
        g.add((HSR[cls_name], RDF.type, RDFS.Class))

    # Element — подкласс LightCone, Character и Enemies
    g.add((HSR.Element, RDFS.subClassOf, HSR.LightCone))
    g.add((HSR.Element, RDFS.subClassOf, HSR.Character))
    g.add((HSR.Element, RDFS.subClassOf, HSR.Enemies))

    # Path — подкласс и LightCone, и Character (у конуса есть только путь как сабкласс; у персонажа тоже должен быть сабкласс путь)
    g.add((HSR.Path, RDFS.subClassOf, HSR.LightCone))
    g.add((HSR.Path, RDFS.subClassOf, HSR.Character))

    # Characteristic — подкласс артефакта Set (убрал наследование от LightCone)
    g.add((HSR.Characteristic, RDFS.subClassOf, HSR.Set))

    # Добавить два сабкласса характеристик: MainCharacteristic и SubCharacteristic
    g.add((HSR.MainCharacteristic, RDF.type, RDFS.Class))
    g.add((HSR.SubCharacteristic, RDF.type, RDFS.Class))
    g.add((HSR.MainCharacteristic, RDFS.subClassOf, HSR.Characteristic))
    g.add((HSR.SubCharacteristic, RDFS.subClassOf, HSR.Characteristic))

    g.add((HSR.CavernRelics, RDFS.subClassOf, HSR.Set))
    g.add((HSR.PlanarRelics, RDFS.subClassOf, HSR.Set))

    pathes = [
        "The Preservation", "The Hunt", "The Harmony", "The Abundance",
        "The Nihility", "The Erudition", "The Destruction", "The Remembrance"
    ]
    for p in pathes:
        g.add((HSR[normalize(p)], RDF.type, HSR.Path))

    elements = ["Physical", "Fire", "Ice", "Lightning", "Quantum", "Imaginary", "Wind"]
    for e in elements:
        g.add((HSR[normalize(e)], RDF.type, HSR.Element))

    characteristics = [
        "HP", "HP_percent", "ATK", "ATK_percent", "DEF", "DEF_percent", "Speed", "CritRate", "CritDMG",
        "BreakEffect", "EffectHitRate", "EffectRES", "EnergyRegen"
    ]
    for c in characteristics:
        g.add((HSR[c], RDF.type, HSR.Characteristic))

    properties = {
        "hasPath": (HSR.Character, HSR.Path),
        "hasElement": (HSR.Character, HSR.Element),
        "hasSet": (HSR.Character, HSR.Set),
        "hasSubCharacteristics": (HSR.Character, HSR.Characteristic),
        "recommendedLightCone": (HSR.Character, HSR.LightCone),
        "hasWeakness": (HSR.Enemies, HSR.Element),
        "recommendedSubStats": (HSR.Character, HSR.Characteristic),
        "recommendedTeam": (HSR.Character, HSR.Team),
        "recommendedMainStatBody": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatFeet": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatSphere": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatRope": (HSR.Character, HSR.Characteristic),
        "lightConeHasPath": (HSR.LightCone, HSR.Path),
        "hasAlternativeLightCones": (HSR.Character, HSR.LightCone),
    }

    for prop_name, (domain, range_) in properties.items():
        prop_uri = HSR[prop_name]
        g.add((prop_uri, RDF.type, OWL.ObjectProperty))
        g.add((prop_uri, RDFS.domain, domain))
        g.add((prop_uri, RDFS.range, range_))

    g.serialize(destination=path, format="xml")
    print("✅ Онтология создана.")