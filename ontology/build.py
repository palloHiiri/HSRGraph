from rdflib import Graph, Namespace, RDF, RDFS, OWL
import re

HSR = Namespace("http://example.org/hsr-ontology#")

def normalize(term):
    if not term:
        return ""
    s = term.replace("The ", "").strip()
    s = s.replace("%", "_percent")
    s = re.sub(r'[^0-9A-Za-z_]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def build_ontology(path):
    g = Graph()
    g.bind("hsr", HSR)

    base_classes = ["Character", "Enemies", "LightCone", "Path", "Element", "Set", "Characteristic"]
    for cls_name in base_classes:
        g.add((HSR[cls_name], RDF.type, RDFS.Class))

    g.add((HSR.CavernRelics, RDF.type, RDFS.Class))
    g.add((HSR.PlanarRelics, RDF.type, RDFS.Class))
    g.add((HSR.CavernRelics, RDFS.subClassOf, HSR.Set))
    g.add((HSR.PlanarRelics, RDFS.subClassOf, HSR.Set))

    g.add((HSR.Characteristic, RDF.type, RDFS.Class))

    g.add((HSR.Element, RDFS.subClassOf, HSR.LightCone))
    g.add((HSR.Element, RDFS.subClassOf, HSR.Character))
    g.add((HSR.Element, RDFS.subClassOf, HSR.Enemies))
    g.add((HSR.Path, RDFS.subClassOf, HSR.LightCone))
    g.add((HSR.Path, RDFS.subClassOf, HSR.Character))

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
        g.add((HSR[normalize(c)], RDF.type, HSR.Characteristic))

    properties = {
        "hasPath": (HSR.Character, HSR.Path),
        "hasElement": (HSR.Character, HSR.Element),
        "hasCavernRelic": (HSR.Character, HSR.CavernRelics),
        "hasPlanarRelic": (HSR.Character, HSR.PlanarRelics),
        "hasSubCharacteristics": (HSR.Character, HSR.Characteristic),
        "recommendedLightCone": (HSR.Character, HSR.LightCone),
        "hasWeakness": (HSR.Enemies, HSR.Element),
        "recommendedSubStats": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatBody": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatFeet": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatSphere": (HSR.Character, HSR.Characteristic),
        "recommendedMainStatRope": (HSR.Character, HSR.Characteristic),
        "lightConeHasPath": (HSR.LightCone, HSR.Path),
        "hasAlternativeLightCones": (HSR.Character, HSR.LightCone),
        "sourceURL": (HSR.Set, RDFS.Literal),  
    }

    for prop_name, (domain, range_) in properties.items():
        prop_uri = HSR[prop_name]
      
        if prop_name == "sourceURL":
            g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            g.add((prop_uri, RDFS.domain, domain))
          
        else:
            g.add((prop_uri, RDF.type, OWL.ObjectProperty))
            g.add((prop_uri, RDFS.domain, domain))
            g.add((prop_uri, RDFS.range, range_))

    g.serialize(destination=path, format="xml")
    print("Онтология создана.")