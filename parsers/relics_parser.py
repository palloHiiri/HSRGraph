from typing import Optional
import requests
from bs4 import BeautifulSoup
from rdflib import Graph, Namespace, RDF, RDFS, Literal

HSR = Namespace("http://example.org/hsr-ontology#")


def normalize(term: str) -> str:
    """Нормализация имени для URI: убираем 'The ', пробелы и косые."""
    if not term:
        return ""
    return term.strip().replace(" ", "_").replace("/", "_").replace('"', "").replace("\"" , "")


def _extract_set_name_from_td(td) -> Optional[str]:
    """
    Извлекает имя набора строго из текста первой ссылки <a> внутри td.
    Если ссылки нет — возвращает None (требование: парсить только текст ссылки).
    """
    if td is None:
        return None
    a = td.find("a")
    if a and a.text and a.text.strip():
        return a.text.strip()
    return None


def _extract_link_from_td(td) -> Optional[str]:
    """Вернуть href первой ссылки внутри td, если есть."""
    if td is None:
        return None
    a = td.find("a", href=True)
    if a:
        return a["href"].strip()
    return None


def parse_relics(graph: Graph, url: str) -> Graph:
    """
    Парсит страницу Game8 с реликвиями и добавляет данные в graph.
    Важное изменение: имя набора берётся ТОЛЬКО из текста первой ссылки в первом столбце.
    Картинки не используются и не добавляются в онтологию.
    """
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    for h3 in soup.find_all("h3"):
        heading = h3.get_text(separator=" ", strip=True)
        if "Cavern" in heading or "Cavern Relic" in heading:
            relic_class = HSR.CavernRelics
            section_name = "Cavern"
        elif "Planar" in heading or "Planar Ornament" in heading or "Ornament" in heading:
            relic_class = HSR.PlanarRelics
            section_name = "Planar"
        else:
            continue

        table = h3.find_next("table")
        if table is None:
            continue

        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")

        # Пропускаем заголовок таблицы (строки с <th>)
        data_rows = [r for r in rows if not r.find_all("th")]

        for tr in data_rows:
            tds = tr.find_all("td")
            if not tds:
                continue

            # Получаем имя исключительно из текста <a> в первом столбце
            name = _extract_set_name_from_td(tds[0])
            if not name:
                # Если ссылки нет — пропускаем (по требованию парсить только текст ссылки)
                continue

            norm_name = normalize(name)
            set_uri = HSR[norm_name]

            # Добавляем типы — Set и соответствующий подкласс (Cavern/Planar)
            graph.add((set_uri, RDF.type, HSR.Set))
            graph.add((set_uri, RDF.type, relic_class))

            # Эффект набора обычно во втором столбце
            effect_text = ""
            if len(tds) >= 2:
                effect_text = tds[1].get_text(separator=" ", strip=True)
            if effect_text:
                graph.add((set_uri, RDFS.comment, Literal(effect_text)))

            # Сохраняем ссылку на конкретный пост набора, если она есть в <a>
            specific_link = _extract_link_from_td(tds[0])
            if specific_link:
                graph.add((set_uri, HSR.sourceURL, Literal(specific_link)))
            else:
                graph.add((set_uri, HSR.sourceURL, Literal(url)))

            print(f"🗃️ {section_name} набор: '{name}' -> HSR:{norm_name}")

    return graph