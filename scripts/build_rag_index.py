from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "exports" / "rag_documents.jsonl"
INDEX_PATH = ROOT / "rag_index_matrix.npz"
VECTORIZER_PATH = ROOT / "rag_vectorizer.pkl"
META_PATH = ROOT / "rag_index_meta.json"


def load_documents(path: Path) -> list[dict]:
    documents: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            documents.append({
                "id": obj["id"],
                "text": obj["text"],
                "metadata": obj["metadata"],
            })
    return documents


def make_search_text(doc: dict) -> str:
    metadata = doc["metadata"]
    title = str(metadata.get("title", "") or "")
    subject = str(metadata.get("subject", "") or "")
    class_level = str(metadata.get("class_level", "") or "")
    difficulty = str(metadata.get("difficulty", "") or "")
    tags = " ".join(str(tag) for tag in metadata.get("tags", []) if tag)
    source_ids = " ".join(str(source_id) for source_id in metadata.get("source_ids", []) if source_id)

    # Use the full original text and a compact metadata summary so retrieval is stronger on real classroom concepts.
    text = str(doc.get("text", "") or "")
    summary = " ".join(item for item in [title, subject, class_level, difficulty, tags, source_ids] if item)
    return f"{text} {summary}"


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"RAG export not found: {INPUT_PATH}")

    documents = load_documents(INPUT_PATH)
    if not documents:
        raise ValueError(f"No documents found in {INPUT_PATH}")

    texts = [make_search_text(doc) for doc in documents]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        strip_accents="unicode",
    )
    matrix = vectorizer.fit_transform(texts)

    sparse.save_npz(str(INDEX_PATH), matrix)
    with VECTORIZER_PATH.open("wb") as handle:
        pickle.dump(vectorizer, handle)
    META_PATH.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Indexed {len(documents)} documents into {INDEX_PATH}.")
    print(f"Saved vectorizer to {VECTORIZER_PATH}.")
    print(f"Metadata saved to {META_PATH}.")


if __name__ == "__main__":
    main()
