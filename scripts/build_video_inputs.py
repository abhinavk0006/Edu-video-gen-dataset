"""Create records that map directly to the current notebook's three inputs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chemistry_experiments.json"
EXPORT_PATH = ROOT / "exports" / "video_inputs.jsonl"


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EXPORT_PATH.open("w", encoding="utf-8") as handle:
        for record in payload["experiments"]:
            procedure = " ".join(
                f"Step {step['step_id']}: {step['instruction']}"
                for step in record["procedure_steps"]
            )
            image = next(
                asset for asset in record["image_assets"]
                if asset["role"] == "starting_image"
            )
            output = {
                "experiment_id": record["experiment_id"],
                "USER_INPUT": (
                    f"Show a school chemistry experiment called '{record['title']}' "
                    f"for Class {record['class_level']}. Goal: {record['educational_goal']} "
                    f"Materials: {', '.join(record['materials'])}. {procedure}"
                ),
                "EXPERIMENT_LABEL": record["experiment_id"],
                "STARTING_IMAGE_URL": image["url"],
                "source_status": record["status"],
            }
            handle.write(json.dumps(output, ensure_ascii=False) + "\n")
    print(f"Built notebook-compatible inputs for {len(payload['experiments'])} experiments.")


if __name__ == "__main__":
    main()
