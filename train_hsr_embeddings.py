import os
import pickle

import numpy as np
import rdflib
import torch
from pykeen.models import TransE
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

try:
    import torch_directml
except ImportError:
    torch_directml = None

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    from sklearn.manifold import TSNE
    from sklearn.decomposition import PCA
except ImportError:
    TSNE = None
    PCA = None


def train_graph_embeddings(rdf_file_path: str,
                           save_dir: str = "hsr_embedding_results"):

    print(f"1. Загрузка графа из {rdf_file_path}...")
    g = rdflib.Graph()
    g.parse(rdf_file_path, format="xml")
    print(f"   Загружено триплетов: {len(g)}")

    print("2. Подготовка данных для PyKEEN...")
    triples = []
    for s, p, o in g:
        triples.append([str(s), str(p), str(o)])
    triples = np.array(triples, dtype=str)

    tf = TriplesFactory.from_labeled_triples(triples)
    training, testing = tf.split([0.8, 0.2], random_state=42)
    print(f"   Сущностей: {len(tf.entity_to_id)}, отношений: {len(tf.relation_to_id)}")


    os.makedirs(save_dir, exist_ok=True)

    result = pipeline(
        training=training,
        testing=testing,
        model="TransE",
        model_kwargs=dict(embedding_dim=50),     
        training_kwargs=dict(num_epochs=50),     
        random_seed=42,
        device=device,
    )

    print("   Обучение завершено.")

    result.save_to_directory(save_dir)

    tf_path = os.path.join(save_dir, "triples_factory.pkl")
    with open(tf_path, "wb") as f:
        pickle.dump(tf, f)
    print(f"4. Результаты сохранены в папку '{save_dir}'")

    return result.model, tf


def load_saved_model(directory: str = "hsr_embedding_results"):
    """
    Загружает сохранённую модель TransE и TriplesFactory.
    """
    from pykeen.models import TransE as TransEModel
    
    print(f"Загрузка модели из {directory}...")
    
    model = TransEModel.load(os.path.join(directory, "model.pkl"))
    
    tf_path = os.path.join(directory, "triples_factory.pkl")
    with open(tf_path, "rb") as f:
        tf = pickle.load(f)
    
    print("Модель загружена успешно.")
    return model, tf

def get_entity_embedding(entity_uri: str, model, tf):
    """
    Получает эмбеддинг для сущности по её URI.
    """
    try:
        entity_id = tf.entity_to_id[entity_uri]
        embedding = model.entity_representations[0](indices=torch.tensor([entity_id])).detach().numpy()[0]
        return embedding
    except KeyError:
        print(f"Сущность {entity_uri} не найдена в графе.")
        return None


def get_relation_embedding(relation_uri: str, model, tf):
    """
    Получает эмбеддинг для отношения по его URI.
    """
    try:
        relation_id = tf.relation_to_id[relation_uri]
        embedding = model.relation_representations[0](indices=torch.tensor([relation_id])).detach().numpy()[0]
        return embedding
    except KeyError:
        print(f"Отношение {relation_uri} не найдено в графе.")
        return None


def find_similar_entities(entity_uri: str, model, tf, top_k: int = 5):
    """
    Находит top_k похожих сущностей по косинусному расстоянию.
    """
    from sklearn.metrics.pairwise import cosine_similarity
    
    entity_embedding = get_entity_embedding(entity_uri, model, tf)
    if entity_embedding is None:
        return []
    
    all_entity_ids = torch.arange(len(tf.entity_to_id))
    all_embeddings = model.entity_representations[0](indices=all_entity_ids).detach().numpy()
    
    similarities = cosine_similarity([entity_embedding], all_embeddings)[0]
    
    top_indices = np.argsort(similarities)[::-1][1:top_k+1]
    
    results = []
    id_to_entity = {v: k for k, v in tf.entity_to_id.items()}
    for idx in top_indices:
        similar_entity = id_to_entity[idx]
        similarity = similarities[idx]
        results.append((similar_entity, similarity))
    
    return results


def reduce_embeddings(embeddings,
                      method: str = "tsne",
                      random_state: int = 42,
                      perplexity: int = 30):
    """
    Сжать эмбеддинги в 2D с помощью t-SNE или PCA.
    """
    if method == "pca":
        if PCA is None:
            raise ImportError("Скрипт запущен без scikit-learn. Установи scikit-learn для PCA.")
        reducer = PCA(n_components=2, random_state=random_state)
    else:
        if TSNE is None:
            raise ImportError("Скрипт запущен без scikit-learn. Установи scikit-learn для t-SNE.")
        n_samples = len(embeddings)
        if n_samples < 2:
            raise ValueError("Слишком мало точек для t-SNE: нужно хотя бы 2 сущности.")
        safe_perplexity = min(perplexity, n_samples - 1)
        reducer = TSNE(
            n_components=2,
            random_state=random_state,
            perplexity=safe_perplexity,
            init="pca",
            learning_rate="auto",
        )

    return reducer.fit_transform(embeddings)


def collect_all_embeddings(model, tf):
    """
    Собирает все эмбеддинги сущностей из модели.
    Возвращает: (embeddings, labels)
    """
    all_entity_ids = torch.arange(len(tf.entity_to_id))
    embeddings = model.entity_representations[0](indices=all_entity_ids).detach().numpy()
    
    id_to_entity = {v: k for k, v in tf.entity_to_id.items()}
    labels = [id_to_entity[i] for i in range(len(embeddings))]
    
    return embeddings, labels

def plot_embeddings_2d(points_2d,
                       labels,
                       title: str = "Embedding map",
                       max_labels: int = 75,
                       save_path: str | None = None,
                       figsize=(12, 10)):

    if plt is None:
        raise ImportError("matplotlib не установлен. Установи matplotlib для визуализации.")

    plt.figure(figsize=figsize)
    plt.scatter(points_2d[:, 0], points_2d[:, 1], s=12, alpha=0.6)

    def _shorten(uri: str) -> str:
        if "#" in uri:
            return uri.split("#")[-1]
        return uri

    for i, label in enumerate(labels[:max_labels]):
        short = _shorten(label)
        plt.annotate(short, (points_2d[i, 0], points_2d[i, 1]), fontsize=8, alpha=0.7)

    plt.title(title)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200)
        print(f"График сохранён в {save_path}")
    else:
        plt.show()


def visualize_embeddings(model: TransE,
                         triples_factory: TriplesFactory,
                         method: str = "tsne",
                         max_labels: int = 75,
                         save_path: str = "hsr_embedding_results/embeddings.png",
                         perplexity: int = 30,
                         max_points: int = 1200,
                         random_state: int = 42):

    print("5. Подготовка данных для визуализации...")
    embeddings, labels = collect_all_embeddings(model, triples_factory)

    if max_points and len(embeddings) > max_points:
        rng = np.random.default_rng(random_state)
        indices = rng.choice(len(embeddings), size=max_points, replace=False)
        embeddings = embeddings[indices]
        labels = [labels[i] for i in indices]
        print(f"   Всего сущностей: {len(triples_factory.entity_to_id)}, "
              f"визуализируем случайные {len(labels)}.")
    else:
        print(f"   Всего сущностей: {len(labels)}.")

    print(f"   Снижение размерности методом {method}...")
    points_2d = reduce_embeddings(embeddings, method=method, perplexity=perplexity)

    plot_embeddings_2d(
        points_2d,
        labels,
        title=f"HSR Ontology Embeddings ({method.upper()})",
        max_labels=max_labels,
        save_path=save_path,
    )


def find_rdf_file():

    rdf_path = "data/hsr_ontology_clean.rdf"
    if os.path.exists(rdf_path):
        return rdf_path
    
    for file in os.listdir("."):
        if file.endswith(".rdf"):
            return file
    
    raise FileNotFoundError("RDF файл не найден. Ожидается data/hsr_ontology.rdf")


def main():
    save_dir = "hsr_embedding_results"
    
    print("=" * 60)
    print("HSR ONTOLOGY EMBEDDINGS TRAINER")
    print("=" * 60)
    
    try:
        rdf_file = find_rdf_file()
        print(f"\n✓ Найден RDF файл: {rdf_file}")
    except FileNotFoundError as e:
        print(f"\n✗ Ошибка: {e}")
        return
    
    if os.path.exists(save_dir) and os.path.exists(os.path.join(save_dir, "model.pkl")):
        print(f"✓ Найдена сохранённая модель в {save_dir}")
        model, tf = load_saved_model(save_dir)
    else:
        print(f"\n→ Обученная модель не найдена, начинаю обучение...")
        model, tf = train_graph_embeddings(rdf_file, save_dir)
    
    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
    print("=" * 60)
    
    id_to_entity = {v: k for k, v in tf.entity_to_id.items()}
    entity_list = list(id_to_entity.values())
    
    demo_entities = [e for e in entity_list if "http://example.org/hsr-ontology#" in e][:5]
    
    for entity in demo_entities:
        entity_name = entity.split("#")[-1]
        print(f"\n→ Сущность: {entity_name}")
        
        similar = find_similar_entities(entity, model, tf, top_k=3)
        if similar:
            print("  Похожие сущности:")
            for sim_entity, similarity in similar:
                sim_name = sim_entity.split("#")[-1]
                print(f"    • {sim_name}: {similarity:.4f}")
    
    print("\n" + "=" * 60)
    print("ВИЗУАЛИЗАЦИЯ")
    print("=" * 60)
    visualize_embeddings(model, tf, method="tsne", max_labels=75, save_path="hsr_embedding_results/embeddings.png")


if __name__ == "__main__":
    main()
