"""Retrieve experiments and build source-grounded video prompt bundles."""
from __future__ import annotations

import argparse
import json
import pickle
import re
from pathlib import Path
from typing import Any

from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity

from query_rag import rank_documents

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chemistry_experiments.json"
INDEX_PATH = ROOT / "rag_index_matrix.npz"
VECTORIZER_PATH = ROOT / "rag_vectorizer.pkl"
META_PATH = ROOT / "rag_index_meta.json"
DEFAULT_OUTPUT = ROOT / "exports" / "rag_prompt_bundle.json"


def load_canonical_records() -> dict[str, dict[str, Any]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return {record["experiment_id"]: record for record in payload["experiments"]}


def load_index() -> tuple[Any, Any, list[dict[str, Any]]]:
    required = [INDEX_PATH, VECTORIZER_PATH, META_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "RAG index files not found. Run scripts\\build_rag_index.py first: "
            + ", ".join(missing)
        )

    with VECTORIZER_PATH.open("rb") as handle:
        vectorizer = pickle.load(handle)
    matrix = sparse.load_npz(str(INDEX_PATH))
    documents = json.loads(META_PATH.read_text(encoding="utf-8"))
    return vectorizer, matrix, documents


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def make_step_prompt(record: dict[str, Any], scene: dict[str, Any], step: dict[str, Any]) -> str:
    materials = ", ".join(record.get("materials", []))
    visible_actions = ", ".join(scene.get("visible_actions", []))
    return (
        f"Create a realistic educational science video clip for Class {record['class_level']} "
        f"{record['subject']} experiment '{record['title']}'. "
        f"Show the scene '{scene['name']}': {scene['description']} "
        f"Perform this step: {step['instruction']} "
        f"Show the expected observation: {step['observation']} "
        f"Visible actions may include: {visible_actions}. "
        f"Use only these materials: {materials}. "
        "Keep the apparatus, quantities, actions, and scientific outcome accurate. "
        "Use clear classroom lighting, stable framing, natural motion, and no labels or watermark."
    )


def build_bundle(query: str, top_k: int) -> dict[str, Any]:
    vectorizer, matrix, documents = load_index()
    records = load_canonical_records()
    ranked = rank_documents(query, vectorizer, matrix, documents, top_n=top_k)
    experiments: list[dict[str, Any]] = []
    prompt_inputs: list[dict[str, Any]] = []

    for result in ranked:
        experiment_id = result["id"]
        record = records.get(experiment_id)
        if record is None:
            continue

        scenes = record.get("scenes", [])
        procedure_steps = record.get("procedure_steps", [])
        scene_steps: list[dict[str, Any]] = []
        for step_index, step in enumerate(procedure_steps):
            scene = scenes[min(step_index, len(scenes) - 1)] if scenes else {
                "scene_id": "scene_1",
                "name": "Procedure",
                "description": record["title"],
                "visible_actions": [],
            }
            image_asset = next(
                (
                    asset for asset in record.get("image_assets", [])
                    if asset.get("image_asset_id") == scene.get("image_asset_id")
                ),
                None,
            )
            if image_asset is None:
                image_asset = next(
                    (
                        asset for asset in record.get("image_assets", [])
                        if asset.get("role") == "starting_image"
                    ),
                    {},
                )
            prompt_input = {
                "experiment_id": experiment_id,
                "scene_id": scene["scene_id"],
                "step_id": step["step_id"],
                "prompt": make_step_prompt(record, scene, step),
                "negative_prompt": "blurry, distorted apparatus, incorrect measurements, text artifacts, watermark",
                "starting_image": image_asset.get("url", ""),
                "source_ids": [source["source_id"] for source in record.get("sources", [])],
            }
            scene_steps.append(prompt_input)
            prompt_inputs.append(prompt_input)

        if not procedure_steps:
            for scene in scenes:
                step = {
                    "step_id": f"{scene['scene_id']}_overview",
                    "instruction": scene["description"],
                    "observation": "; ".join(scene.get("visible_actions", [])),
                }
                prompt_input = {
                    "experiment_id": experiment_id,
                    "scene_id": scene["scene_id"],
                    "step_id": step["step_id"],
                    "prompt": make_step_prompt(record, scene, step),
                    "negative_prompt": "blurry, distorted apparatus, text artifacts, watermark",
                    "starting_image": "",
                    "source_ids": [source["source_id"] for source in record.get("sources", [])],
                }
                scene_steps.append(prompt_input)
                prompt_inputs.append(prompt_input)

        scene_bundle = [{
            "scene_id": scene["scene_id"],
            "scene_name": scene["name"],
            "description": scene["description"],
        } for scene in scenes]

        experiments.append({
            "experiment_id": experiment_id,
            "retrieval_score": result["score"],
            "title": record["title"],
            "subject": record["subject"],
            "class_level": record["class_level"],
            "difficulty": record["difficulty"],
            "educational_goal": record["educational_goal"],
            "status": record.get("status"),
            "source_ids": [source["source_id"] for source in record.get("sources", [])],
            "scenes": scene_bundle,
        })

    return {
        "query": query,
        "top_k": top_k,
        "retrieved_experiments": experiments,
        "prompt_inputs": prompt_inputs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve NCERT experiments and create grounded video prompts."
    )
    parser.add_argument("query", help="Natural-language experiment query.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of experiments to retrieve.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="JSON bundle output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("--top-k must be at least 1")

    bundle = build_bundle(args.query, args.top_k)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Retrieved {len(bundle['retrieved_experiments'])} experiments.")
    print(f"Built {len(bundle['prompt_inputs'])} scene-step prompts.")
    print(f"Saved prompt bundle to {output_path}")


if __name__ == "__main__":
    main()
