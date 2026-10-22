"""Attach explicit draft scientific/rendering requirements to every record.

This is a planning enrichment, not a source for missing numerical parameters.
Run after apply_ncert_quantities.py and before rebuilding the exports.
"""
import json
from pathlib import Path
from science_contract import science_contract

ROOT = Path(__file__).resolve().parents[1]


def enrich(record):
    chemistry = record["subject"] == "Chemistry"
    requirements = (["reagent identity and concentration", "dose or endpoint for each addition",
                     "initial sample state and volume", "vessel capacity and safe working volume"]
                    if chemistry else ["apparatus dimensions and ratings", "measurement range and least count",
                                      "controlled settings and measured variables", "reviewed physical arrangement or circuit connections"])
    record["rendering_contract"] = {
        "version": 1, "review_status": "draft", "source_reviewed": False,
        "quantity_coverage": record.get("quantity_review", {}).get("coverage", "not_covered"),
        "required_source_details": requirements,
        "numeric_values_inferred": False,
        "continuity_policy": "Preserve the last state of each identified sample/apparatus; allocate a separate reference for a fresh sample or changed setup.",
        "observation_policy": "Show only the selected source's conditional observation on its named target, after its documented cause.",
        "pacing_policy": "Split separate actions; retain laboratory waiting/heating times as process conditions, not compressed clip durations.",
        "physics_status": "not_applicable" if chemistry else "awaiting_manual_and_validation",
        "render_mode_policy": "Choose the rendering mode after reviewing the actual setup. Circuit diagrams require explicit validated topology; never infer it from a title.",
    }
    groups = [record["procedure_steps"]] + [v["procedure_steps"] for v in record.get("protocol_variants", [])]
    for steps in groups:
        for step in steps:
            step["science_spec"] = science_contract(record, step)
            # Absence of a source quantity is explicit in every record, including legacy entries.
            step.setdefault("quantities", [])
            if not chemistry:
                step.setdefault("render_mode", "wan")
    return record


def main():
    path=ROOT/"data/chemistry_experiments.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    for record in data["experiments"]:
        enrich(record)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Enriched scientific/rendering contracts for all {len(data['experiments'])} records; missing values remain unset.")


if __name__ == "__main__":
    main()
