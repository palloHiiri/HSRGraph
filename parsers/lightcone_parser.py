import requests
from bs4 import BeautifulSoup
from rdflib import Namespace, RDF
import re

HSR = Namespace("http://example.org/hsr-ontology#")

def normalize(term):
    return term.replace("The ", "").replace(" ", "_")

def parse_light_cones(graph, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Находим заголовок
    header = soup.find("h3", string=re.compile("Available Light Cones", re.IGNORECASE))
    if not header:
        print("❌ Заголовок 'Available Light Cones' не найден.")
        return

    # Переходим к div после заголовка
    div = header.find_next_sibling("div")
    if not div:
        print("❌ <div> после заголовка не найден.")
        return

    # Переходим к таблице после div
    table = div.find_next_sibling("table")
    if not table:
        print("❌ Таблица после <div> не найдена.")
        return

    # Получаем все строки таблицы
    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 3:
            continue  # пропускаем заголовки и неполные строки

        # Название конуса (1-й столбец)
        cone_name = cells[0].get_text(strip=True)

        # Путь (3-й столбец)
        path_raw = cells[2].get_text(strip=True)
        path = normalize(path_raw)

        # Добавление в граф
        cone_uri = HSR[normalize(cone_name)]
        graph.add((cone_uri, RDF.type, HSR.LightCone))
        graph.add((cone_uri, HSR.lightConeHasPath, HSR[path]))

        print(f"🔷 {cone_name} → {path_raw}")
