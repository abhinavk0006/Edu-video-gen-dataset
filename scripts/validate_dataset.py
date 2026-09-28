"""Validate the canonical dataset with no third-party dependencies."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chemistry_experiments.json"
REQUIRED = {
    "experiment_id", "subject", "class_level", "title", "difficulty",
    "educational_goal", "materials", "procedure_steps", "scenes",
    "sources", "image_assets", "status",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> None:
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {DATA_PATH}: {exc}")

    records = payload.get("experiments") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not records:
        fail("top-level 'experiments' must be a non-empty array")

    ids: set[str] = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            fail(f"record {index} is not an object")
        missing = REQUIRED - record.keys()
        if missing:
            fail(f"record {index} is missing: {', '.join(sorted(missing))}")
        experiment_id = record["experiment_id"]
        if experiment_id in ids:
            fail(f"duplicate experiment_id: {experiment_id}")
        ids.add(experiment_id)
        if record["subject"] not in {"Chemistry", "Physics"}:
            fail(f"{experiment_id}: subject must be Chemistry or Physics")
        if record["class_level"] not in {8, 9, 10, 11, 12}:
            fail(f"{experiment_id}: class_level must be 8-12")
        if len(record["procedure_steps"]) < 3:
            fail(f"{experiment_id}: add at least three procedure steps")
        if len(record["scenes"]) < 1:
            fail(f"{experiment_id}: add at least one scene")
        if len(record["sources"]) < 1:
            fail(f"{experiment_id}: add at least one source")
        for scene in record["scenes"]:
            if scene["image_asset_id"] not in {asset["image_asset_id"] for asset in record["image_assets"]}:
                fail(f"{experiment_id}: scene references unknown image asset")

    classes = sorted({record["class_level"] for record in records})
    print(f"Validated {len(records)} records across Classes {', '.join(map(str, classes))}.")
    print(f"All experiment IDs are unique and all scene image references resolve.")


if __name__ == "__main__":
    main()
