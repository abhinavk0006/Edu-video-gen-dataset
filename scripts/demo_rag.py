from __future__ import annotations

import json
import pickle
from pathlib import Path

from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "rag_index_matrix.npz"
VECTORIZER_PATH = ROOT / "rag_vectorizer.pkl"
META_PATH = ROOT / "rag_index_meta.json"

QUERY_SYNONYMS = {
    "acid base": "acid base neutralisation neutralization titration ph",
    "acid-base": "acid base neutralisation neutralization titration ph",
    "ohm": "ohm resistance current voltage circuit resistor potential difference conductor wire meter bridge ammeter voltmeter",
    "ohm's": "ohm resistance current voltage circuit resistor potential difference conductor wire meter bridge ammeter voltmeter",
    "ohm law": "ohm law resistance current voltage circuit resistor potential difference conductor wire meter bridge ammeter voltmeter",
    "law of ohm": "ohm law resistance current voltage circuit resistor potential difference conductor wire meter bridge ammeter voltmeter",
    "resistance": "resistance resistor ohm circuit voltage current potential difference conductor wire meter bridge ammeter voltmeter",
    "potential difference": "potential difference resistance current voltage circuit resistor conductor wire meter bridge ammeter voltmeter",
    "voltage": "voltage circuit resistor current electrical potential conductor wire meter bridge ammeter voltmeter",
    "current": "current voltage resistance circuit conductor wire meter bridge ammeter voltmeter",
    "circuit": "circuit current voltage resistance conductor wire meter bridge ammeter voltmeter",
    "law of conservation": "conservation mass chemical reaction matter",
    "diffusion": "diffusion spread mixing solution particles",
    "titration": "titration neutralization acid base volume concentration",
    "reaction rate": "reaction rate temperature concentration catalyst kinetics",
    "ph": "ph acidity alkalinity indicator base acid",
}


def expand_query(query: str) -> str:
    lowered = query.lower()
    expanded = lowered
    for key, value in QUERY_SYNONYMS.items():
        if key in lowered:
            expanded = f"{expanded} {value}"
    return expanded


def load_data() -> tuple[pickle.Pickler, object, list[dict]]:
    with VECTORIZER_PATH.open("rb") as handle:
        vectorizer = pickle.load(handle)
    matrix = sparse.load_npz(str(INDEX_PATH))
    documents = json.loads(META_PATH.read_text(encoding="utf-8"))
    return vectorizer, matrix, documents


def search(query: str, vectorizer, matrix, documents, top_n: int = 5):
    query_text = expand_query(query)
    qv = vectorizer.transform([query_text])
    scores = cosine_similarity(qv, matrix).flatten()
    top_idx = scores.argsort()[-top_n:][::-1]

    results = []
    for idx in top_idx:
        doc = documents[int(idx)]
        meta = doc["metadata"]
        results.append({
            "score": round(float(scores[idx]), 4),
            "id": doc["id"],
            "title": meta.get("title"),
            "subject": meta.get("subject"),
            "class_level": meta.get("class_level"),
            "difficulty": meta.get("difficulty"),
        })
    return results


def main() -> None:
    if not INDEX_PATH.exists() or not VECTORIZER_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError("RAG index files are missing. Run build_rag_index.py first.")

    vectorizer, matrix, documents = load_data()
    print("Science experiment RAG demo")
    print("Type 'q' or 'quit' to exit.\n")

    while True:
        query = input("Search: ").strip()
        if query.lower() in {"q", "quit", "exit"}:
            print("Goodbye.")
            break

        results = search(query, vectorizer, matrix, documents)
        print(f"\nTop results for: {query}\n")
        if not results:
            print("No results found.")
            continue

        for item in results:
            print(f"{item['score']:.4f} | {item['id']} | {item['title']} | {item['subject']} | class {item['class_level']} | {item['difficulty']}")
        print()


if __name__ == "__main__":
    main()
