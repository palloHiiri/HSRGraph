"""
Скрипт для очистки RDF файла от sourceURL и rdfs:comment триплетов.
sourceURL и длинные комментарии засоряют эмбеддинги, так как добавляют ненужные "сущности".
"""

import rdflib
from rdflib import Namespace, RDFS

HSR = Namespace("http://example.org/hsr-ontology#")

def clean_rdf(input_file: str, output_file: str):
    """
    Загружает RDF, удаляет все триплеты с sourceURL и rdfs:comment, сохраняет.
    """
    from rdflib import RDFS
    
    print(f"Загрузка {input_file}...")
    g = rdflib.Graph()
    g.parse(input_file, format="xml")
    print(f"Загружено триплетов: {len(g)}")
    
    # Находим все триплеты с sourceURL
    source_url_triples = list(g.triples((None, HSR.sourceURL, None)))
    print(f"Найдено триплетов с sourceURL: {len(source_url_triples)}")
    
    # Удаляем их
    for s, p, o in source_url_triples:
        g.remove((s, p, o))
    
    # Находим все триплеты с rdfs:comment (длинные описания эффектов артефактов)
    comment_triples = list(g.triples((None, RDFS.comment, None)))
    print(f"Найдено триплетов с rdfs:comment: {len(comment_triples)}")
    
    # Удаляем и их
    for s, p, o in comment_triples:
        g.remove((s, p, o))
    
    print(f"Осталось триплетов: {len(g)}")
    
    # Сохраняем
    g.serialize(output_file, format="xml", encoding="utf-8")
    print(f"Сохранено в {output_file}")
    
    return len(source_url_triples) + len(comment_triples)


if __name__ == "__main__":
    input_path = "data/hsr_ontology.rdf"
    output_path = "data/hsr_ontology_clean.rdf"
    
    removed = clean_rdf(input_path, output_path)
    print(f"\n✓ Удалено триплетов: {removed}")
    print(f"✓ Чистый файл готов: {output_path}")
    print("\nТеперь замени старый файл или используй новый в скриптах:")
    print("  - mv data/hsr_ontology_clean.rdf data/hsr_ontology.rdf")
