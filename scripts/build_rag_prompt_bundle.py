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
from quantity_contract import STEP_FIELDS, quantity_payload, select_protocol
from science_contract import science_contract

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chemistry_experiments.json"
INDEX_PATH = ROOT / "rag_index_matrix.npz"
VECTORIZER_PATH = ROOT / "rag_vectorizer.pkl"
META_PATH = ROOT / "rag_index_meta.json"
DEFAULT_OUTPUT = ROOT / "exports" / "rag_prompt_bundle.json"
REVIEWED_STATUSES = {"verified", "reviewed", "approved"}
PLACEHOLDER_TEXT = re.compile(
    r"record the visible result|described by the manual|where prescribed|"
    r"not specified|needs? verification|placeholder|to be confirmed",
    re.IGNORECASE,
)
ACTION_VERBS = re.compile(
    r"\b(add|mix|stir|heat|warm|cool|filter|wash|dry|weigh|transfer|"
    r"dissolve|pour|decant|titrate|measure|test|record|rinse|hold|"
    r"swirl|introduce|separate|concentrate|crystallize)\b",
    re.IGNORECASE,
)
SEQUENCE_MARKERS = re.compile(r"\b(then|followed by|after that|subsequently)\b", re.IGNORECASE)


def requires_clip_split(instruction: str) -> bool:
    """Flag combined deliberate operations, excluding passive results like dissolution."""
    actions = [verb.lower() for verb in ACTION_VERBS.findall(instruction)
               if verb.lower() not in {"dissolve", "record", "test"}]
    return len(actions) >= 2 or bool(SEQUENCE_MARKERS.search(instruction))


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


def review_reasons(record: dict[str, Any], step: dict[str, Any]) -> list[str]:
    """Expose source gaps instead of presenting draft data as verified procedure."""
    reasons: list[str] = []
    status = str(record.get("status", "")).strip().lower()
    if status not in REVIEWED_STATUSES:
        reasons.append(f"Experiment source status is {status or 'unspecified'}.")
    for fact in step.get("quantities", []):
        if fact.get("qualifier") in {"not_specified", "range", "approximate"}:
            reasons.append(f"Resolve or explicitly approve {fact['qualifier']} quantity for {fact['reagent']} before numeric dose planning.")
    if record.get("quantity_review", {}).get("coverage") == "partial":
        reasons.append("Aggregate protocol coverage is partial; review the selected branch and its prerequisites.")
    for field, label in (("instruction", "procedure"), ("observation", "observation")):
        value = str(step.get(field, "")).strip()
        if not value or PLACEHOLDER_TEXT.search(value):
            reasons.append(f"The {label} text is missing or generic and needs manual verification.")
    instruction = str(step.get("action", step.get("instruction", "")))
    if requires_clip_split(instruction):
        reasons.append("This step combines multiple visible operations; split it into shorter clips before generation.")
    return reasons


def make_step_prompt(record: dict[str, Any], scene: dict[str, Any], step: dict[str, Any]) -> str:
    instruction = str(step.get("action") or step.get("instruction", "")).strip()
    observation = str(step.get("state_after") or step.get("observation", "")).strip()
    target = str(step.get("target_object", "")).strip()
    quantity = str(step.get("quantity_constraint", "")).strip()
    observable = str(step.get("observable_target", "")).strip()
    pacing = str(step.get("action_pacing", "")).strip()
    preservation = step.get("preserve_objects", [])
    if isinstance(preservation, str):
        preservation = [preservation]
    preservation_text = ", ".join(str(item).strip() for item in preservation if str(item).strip())
    review_needed = review_reasons(record, step)
    constraints = [
        f"Starting state: {step.get('state_before', '')}",
        f"Perform only this procedure step: {instruction}",
        f"End in this documented state: {observation}",
        "Source quantity facts: " + json.dumps({key: step[key] for key in STEP_FIELDS if key in step}, ensure_ascii=False),
    ]
    for label, value in (
        ("Target", target),
        ("Preserve in place", preservation_text),
        ("Quantity", quantity),
        ("Visible observation", observable),
        ("Motion pace", pacing),
    ):
        if value:
            constraints.append(f"{label}: {value}")
    return (
        f"Create a realistic educational science video clip for Class {record['class_level']} "
        f"{record['subject']} experiment '{record['title']}'. "
        f"Show the scene '{scene['name']}'. {' '.join(constraints)} "
        "Use only apparatus already present in the reference image or explicitly named in this step. "
        "Show only this procedure step, acting on its named target; preserve the count and positions of other apparatus. "
        "Depict each observation on the correct physical target. Keep named indicators and measuring devices visible: paper or strips change on the paper, while a liquid indicator changes the sample only when the procedure says it does. "
        "Follow the manual's order and stated quantities; do not invent an exact amount or ratio when none is documented, and never fill a vessel to the rim. "
        "Do not invent a reaction, color change, reagent, or apparatus that the source does not specify. "
        + ("This source has unverified details: depict only explicitly documented actions and results; do not fill gaps by guessing. " if review_needed else "")
        + "Keep the camera fixed, the operation slow and clearly visible, and omit labels and watermarks."
    )


def normalize_step(
    record: dict[str, Any],
    scene: dict[str, Any],
    step: dict[str, Any],
    previous_step: dict[str, Any] | None,
) -> dict[str, Any]:
    """Add safe rendering metadata without guessing hidden physical continuity."""
    explicit_reference = str(step.get("reference_clip", "")).strip()
    continuity = step.get("continuity_required")
    if continuity is None:
        continuity = bool(explicit_reference)
    policy = str(step.get("reference_policy", "")).strip()
    if not policy:
        policy = "previous_state_keyframe" if explicit_reference else "state_keyframe"
    handoff_policy = str(step.get("handoff_policy", "")).strip()
    if not handoff_policy:
        handoff_policy = {
            "mid": "mid",
            "near_end": "near_end",
            "final": "final",
            "offset": "offset",
        }.get(policy, "final" if explicit_reference else "none")
    action = str(step.get("action", step["instruction"])).strip()
    state_before = str(step.get("state_before", "")).strip()
    state_after = str(step.get("state_after", step["observation"])).strip()
    return {
        "step_id": step["step_id"],
        "science_spec": science_contract(record, step),
        "visibility_targets": step.get("visibility_targets", []),
        "handoff_requirements": step.get("handoff_requirements", []),
        "render_mode": step.get("render_mode", "wan"),
        **({"circuit": step["circuit"]} if step.get("circuit") else {}),
        "diagram_timeline": step.get("diagram_timeline", []),
        "state_before": state_before or f"Before: {step['instruction']}",
        "action": action,
        "state_after": state_after,
        "visual_priority": step.get("visual_priority", "normal"),
        "continuity_required": bool(continuity),
        "reference_policy": policy,
        "reference_clip": explicit_reference,
        "reference_mode": "chained" if explicit_reference else "independent",
        "needs_reference_image": not bool(explicit_reference),
        "handoff_policy": handoff_policy,
        "handoff_entity": step.get("handoff_entity", ""),
        "handoff_offset_seconds": step.get("handoff_offset_seconds"),
        "duration_seconds": step.get(
            "duration_seconds",
            step.get("estimated_duration_seconds", 2.0),
        ),
        "reference_image": step.get(
            "reference_image",
            step.get("input_frame_path", ""),
        ),
        "image_prompt": step.get(
            "image_prompt",
            (
                "Create one consistent educational science reference image "
                f"for the starting state: {state_before}. "
                "Show only the apparatus required for this atomic step, with no "
                "duplicate vessels, unrelated equipment, labels, handwriting, or collage."
            ),
        ),
        "target_object": step.get("target_object", ""),
        "preserve_objects": step.get("preserve_objects", []),
        "quantity_constraint": step.get("quantity_constraint", ""),
        "observable_target": step.get("observable_target", ""),
        "action_pacing": step.get("action_pacing", "slow, single deliberate action"),
        "manual_review_required": bool(review_reasons(record, step)),
        "manual_review_reasons": review_reasons(record, step),
        "requires_clip_split": requires_clip_split(str(step.get("action", step.get("instruction", "")))),
        **{key: step[key] for key in STEP_FIELDS if key in step},
    }


def build_bundle(query: str, top_k: int, protocol_selections: dict[str, str] | None = None) -> dict[str, Any]:
    vectorizer, matrix, documents = load_index()
    records = load_canonical_records()
    ranked = rank_documents(query, vectorizer, matrix, documents, top_n=top_k)
    selections = protocol_selections or {}
    if len(selections) > top_k:
        raise ValueError("--top-k must cover all explicitly selected experiments")
    for experiment_id, variant_id in selections.items():
        if experiment_id not in records:
            raise ValueError(f"Unknown explicitly selected experiment {experiment_id}")
        select_protocol(records[experiment_id], variant_id)
    # An explicit experiment/protocol choice pins that record, regardless of
    # vector ranking. Never silently ignore it and render a different experiment.
    ranked = ([{"id": key, "score": 1.0, "method": "explicit_protocol_selection"} for key in selections]
              + [item for item in ranked if item["id"] not in selections])[:top_k]
    experiments: list[dict[str, Any]] = []
    prompt_inputs: list[dict[str, Any]] = []

    for result in ranked:
        experiment_id = result["id"]
        record = records.get(experiment_id)
        if record is None:
            continue

        scenes = record.get("scenes", [])
        selection = (protocol_selections or {}).get(experiment_id)
        procedure_steps = select_protocol(record, selection)
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
            normalized = normalize_step(
                record,
                scene,
                step,
                procedure_steps[step_index - 1] if step_index else None,
            )
            prompt_input = {
                "experiment_id": experiment_id,
                "scene_id": scene["scene_id"],
                "step_id": step["step_id"],
                "prompt": make_step_prompt(record, scene, step),
                "negative_prompt": "blurry, distorted apparatus, incorrect measurements, text artifacts, watermark",
                "starting_image": normalized["reference_image"] or image_asset.get("url", ""),
                "image_prompt": normalized["image_prompt"],
                **normalized,
                "source_ids": [source["source_id"] for source in record.get("sources", [])],
                "source_status": record.get("status", "unspecified"),
                "manual_review_required": bool(normalized["manual_review_required"]),
                "manual_review_reasons": normalized["manual_review_reasons"],
            }
            scene_steps.append(prompt_input)
            prompt_inputs.append(prompt_input)

        if not procedure_steps and not record.get("protocol_variants"):
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
                    "duration_seconds": None,
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
            "retrieval_method": result.get("method", "tfidf"),
            "title": record["title"],
            "subject": record["subject"],
            "class_level": record["class_level"],
            "difficulty": record["difficulty"],
            "educational_goal": record["educational_goal"],
            "status": record.get("status"),
            "manual_review_required": str(record.get("status", "")).strip().lower() not in REVIEWED_STATUSES,
            "source_ids": [source["source_id"] for source in record.get("sources", [])],
            "scenes": scene_bundle,
            "procedure_steps": procedure_steps,
            **quantity_payload(record),
            "selected_protocol_variant": selection or record.get("selected_protocol_variant"),
            "planning_blocked": bool(record.get("protocol_variants") and not procedure_steps),
            "planning_block_reason": "Select one protocol variant before building video steps." if record.get("protocol_variants") and not procedure_steps else "",
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
    parser.add_argument("--protocol", action="append", default=[], metavar="EXPERIMENT_ID=VARIANT_ID", help="Explicit protocol selection; may be repeated. Alternatives are never merged.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("--top-k must be at least 1")

    selections = dict(item.split("=", 1) for item in args.protocol)
    bundle = build_bundle(args.query, args.top_k, selections)
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
