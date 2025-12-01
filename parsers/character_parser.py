import requests
from bs4 import BeautifulSoup
from rdflib import Namespace, RDF

HSR = Namespace("http://example.org/hsr-ontology#")

def normalize(term):
    return term.replace("The ", "").replace(" ", "_")

def parse_characters(graph, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("h3", string="List of All Playable Characters")
    table = table.find_next("table")
    rows = table.find("tbody").find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        name_tag = cells[0].find("a")
        char_name = name_tag.text.strip() if name_tag else cells[0].text.strip()
        element = normalize(cells[2].text.strip())
        path = normalize(cells[3].text.strip())

        char_uri = HSR[normalize(char_name)]
        graph.add((char_uri, RDF.type, HSR.Character))
        graph.add((char_uri, HSR.hasElement, HSR[element]))
        graph.add((char_uri, HSR.hasPath, HSR[path]))

        print(f"👤 {char_name} → {element}, {path}")
