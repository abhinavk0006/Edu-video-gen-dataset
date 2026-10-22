"""Build JSONL files for RAG and downstream prompt generation."""
from __future__ import annotations

import json
from pathlib import Path
from quantity_contract import quantity_payload, quantity_text

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chemistry_experiments.json"
EXPORT_DIR = ROOT / "exports"


def record_to_text(record: dict) -> str:
    steps = "\n".join(
        f"{step['step_id']}. {step['instruction']} Observation: {step['observation']}"
        for step in record["procedure_steps"]
    )
    scenes = "\n".join(
        f"{scene['name']}: {scene['description']} Actions: {', '.join(scene['visible_actions'])}"
        for scene in record["scenes"]
    )
    return "\n".join([
        f"Experiment: {record['title']}",
        f"Class: {record['class_level']}",
        f"Subject: {record['subject']}",
        f"Chapter: {record.get('chapter', '')}",
        f"Goal: {record['educational_goal']}",
        f"Concepts: {', '.join(record.get('concepts', []))}",
        f"Materials: {', '.join(record['materials'])}",
        "Procedure:\n" + steps,
        quantity_text(record),
        "Visual scenes:\n" + scenes,
        f"Tags: {', '.join(record.get('tags', []))}",
    ])


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    records = payload["experiments"]
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with (EXPORT_DIR / "chemistry_experiments.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (EXPORT_DIR / "rag_documents.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            document = {
                "id": record["experiment_id"],
                "text": record_to_text(record),
                # Keep repeated schema keys / evidence boilerplate out of TF-IDF.
                # Full source evidence remains in `text` and canonical records.
                "search_text": " ".join([
                    *([record["title"]] * 4), record["educational_goal"],
                    " ".join(record.get("concepts", [])), " ".join(record["materials"]),
                    " ".join(v["title"] for v in record.get("protocol_variants", [])),
                    " ".join(sorted({
                        f"{fact['reagent']} {fact.get('value', '')} {fact.get('unit', '')} {fact.get('concentration', '')}"
                        for variant in record.get("protocol_variants", [])
                        for step in variant["procedure_steps"] for fact in step.get("quantities", [])
                    })),
                    " ".join(step["instruction"] for step in record["procedure_steps"]) if not record.get("protocol_variants") else "",
                ]),
                "metadata": {
                    "subject": record["subject"],
                    "class_level": record["class_level"],
                    "title": record["title"],
                    "difficulty": record["difficulty"],
                    "tags": record.get("tags", []),
                    "source_ids": [source["source_id"] for source in record["sources"]],
                },
            }
            handle.write(json.dumps(document, ensure_ascii=False) + "\n")

    with (EXPORT_DIR / "prompt_inputs.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            prompt_input = {
                "experiment_id": record["experiment_id"],
                "input": record_to_text(record),
                "scene_count": len(record["scenes"]),
                "image_assets": record["image_assets"],
                **quantity_payload(record),
            }
            handle.write(json.dumps(prompt_input, ensure_ascii=False) + "\n")

    print(f"Built three JSONL exports for {len(records)} experiments in {EXPORT_DIR}.")


if __name__ == "__main__":
    main()
