"""Convert the canonical catalog into the per-file dataset contract."""
from __future__ import annotations

import json
import re
from datetime import date
from collections import Counter
from pathlib import Path
from quantity_contract import STEP_FIELDS, quantity_payload, select_protocol

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "chemistry_experiments.json"
OUTPUT_ROOT = ROOT / "dataset"
DIFFICULTIES = ("easy", "medium", "hard")
MOTION_TYPES = (
    "mechanical_motion",
    "colour_change",
    "state_change",
    "continuous_action",
    "observation",
    "fluid_dynamics",
)


def slug(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value or "experiment"


def motion_type(instruction: str, observation: str) -> str:
    text = f"{instruction} {observation}".lower()
    if any(word in text for word in ("colour", "color", "pink", "blue", "red", "decolour", "precipitate")):
        return "colour_change"
    if any(word in text for word in ("fill", "add", "mix", "heat", "cool", "dissolve", "filter", "pour")):
        return "state_change"
    if any(word in text for word in ("drop", "flow", "rise", "fall", "liquid", "water")):
        return "fluid_dynamics"
    if any(word in text for word in ("observe", "record", "compare", "read", "calculate", "plot")):
        return "observation"
    if any(word in text for word in ("move", "adjust", "rotate", "suspend", "swirl")):
        return "mechanical_motion"
    return "continuous_action"


def prompt_template(kind: str) -> str:
    return kind


def build_scenes(record: dict, image_url: str, image_local: str) -> list[dict]:
    procedures = select_protocol(record)
    groups = [procedures[:1], procedures[1:-1], procedures[-1:]] if len(procedures) > 2 else [procedures]
    groups = [group for group in groups if group]
    scenes = []
    step_number = 1
    for scene_number, group in enumerate(groups, 1):
        scene_id = f"scene_{scene_number}"
        scene_steps = []
        for step in group:
            kind = motion_type(step["instruction"], step["observation"])
            scene_steps.append({
                "step_id": f"{scene_id}_step_{step_number}",
                "step_number": step_number,
                "description": step["instruction"],
                "observation": step["observation"],
                "duration_seconds": 3.0,
                "duration_basis": "Placeholder render budget; not the laboratory process duration. Plan splits and waiting-time cards before generation.",
                "motion_type": kind,
                "moving_objects": record["materials"][:3],
                "key_visual": step["observation"],
                "prompt_template": prompt_template(kind),
                "motion_prompt": "",
                "negative_prompt": "camera movement, blurry, distorted apparatus",
                "generated": False,
                **{key: step[key] for key in STEP_FIELDS if key in step},
            })
            step_number += 1
        scenes.append({
            "scene_id": scene_id,
            "scene_name": ["Setup and Preparation", "Main Procedure", "Observation and Result"][min(scene_number - 1, 2)],
            "new_scene": True,
            "description": record["scenes"][0]["description"],
            "image_url": image_url if scene_number == 1 else "",
            "image_local": image_local if scene_number == 1 else "",
            "image_placeholder": image_url.startswith("PLACEHOLDER"),
            "steps": scene_steps,
        })
    return scenes


def convert_record(record: dict, output_path: Path) -> dict:
    subject = record["subject"].lower()
    difficulty = record["difficulty"]
    image = next(asset for asset in record["image_assets"] if asset["role"] == "starting_image")
    filename = output_path.name
    image_name = f"{slug(record['title'])}_setup.jpg"
    image_local = f"images/{subject}/{image_name}"
    scenes = build_scenes(record, image["url"], image_local)
    all_motion_types = [step["motion_type"] for scene in scenes for step in scene["steps"]]
    output = {
        "id": f"{subject}_{difficulty}_{record['experiment_id']}",
        "name": record["title"],
        "subject": subject,
        "class_level": record["class_level"],
        "difficulty": difficulty,
        "chapter": record.get("chapter", ""),
        "ncert_reference": record["sources"][0]["citation"],
        "source_file": record["sources"][0]["url"],
        "educational_goal": record["educational_goal"],
        "prerequisites": record.get("concepts", []),
        "estimated_video_duration_seconds": int(sum(step["duration_seconds"] for scene in scenes for step in scene["steps"])),
        "tags": record.get("tags", []),
        "materials": record["materials"],
        "safety_notes": record.get("safety_notes", []),
        **quantity_payload(record),
        "procedure_steps": record["procedure_steps"],
        "source_experiment_id": record["experiment_id"],
        "scenes": scenes,
        "prompt_templates_used": sorted(set(all_motion_types)),
        "total_clips": sum(len(scene["steps"]) for scene in scenes),
        "total_scenes": len(scenes),
        "status": "dataset_only",
        "video_generated": False,
        "video_path": "",
        "notes": "Image is a placeholder until a license-reviewed local asset is added." if image["license_status"] == "placeholder" else "",
    }
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main() -> None:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    # Update generated records in place. Never recursively delete images or user files.
    previous_metadata = OUTPUT_ROOT / "metadata.json"
    previous_paths = {}
    if previous_metadata.exists():
        previous = json.loads(previous_metadata.read_text(encoding="utf-8"))
        previous_paths = {entry["id"]: entry["path"] for entry in previous.get("experiments", [])}
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for subject in ("physics", "chemistry"):
        for difficulty in DIFFICULTIES:
            (OUTPUT_ROOT / subject / difficulty).mkdir(parents=True, exist_ok=True)
        (OUTPUT_ROOT / "images" / subject).mkdir(parents=True, exist_ok=True)

    entries = []
    counts = Counter()
    for record in source["experiments"]:
        subject = record["subject"].lower()
        difficulty = record["difficulty"]
        record_key = f"{subject}_{difficulty}_{record['experiment_id']}"
        relative = previous_paths.get(record_key, f"{subject}/{difficulty}/{slug(record['title'])}.json")
        path = OUTPUT_ROOT / relative
        converted = convert_record(record, path)
        counts[(subject, difficulty)] += 1
        entries.append({
            "id": converted["id"],
            "name": converted["name"],
            "subject": subject,
            "class_level": converted["class_level"],
            "difficulty": difficulty,
            "path": path.relative_to(OUTPUT_ROOT).as_posix(),
            "video_generated": False,
            "total_clips": converted["total_clips"],
            "total_scenes": converted["total_scenes"],
        })

    metadata = {
        "version": "1.0",
        "last_updated": date.today().isoformat(),
        "total_experiments": len(entries),
        "subjects": {
            subject: {difficulty: counts[(subject, difficulty)] for difficulty in DIFFICULTIES}
            for subject in ("physics", "chemistry")
        },
        "motion_types": list(MOTION_TYPES),
        "experiments": entries,
    }
    (OUTPUT_ROOT / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(entries)} per-experiment files in {OUTPUT_ROOT}")
    print(json.dumps(metadata["subjects"], indent=2))


if __name__ == "__main__":
    main()
