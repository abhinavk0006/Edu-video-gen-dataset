"""Shared export contract for source-transcribed quantity protocols."""
import json

FIELDS = ("quantity_review", "protocol_variants", "selected_protocol_variant", "rendering_contract")
STEP_FIELDS = ("quantities", "source_evidence", "sample_id", "reaction_scope", "science_spec", "render_mode", "visibility_targets", "handoff_requirements", "circuit", "diagram_timeline")


def quantity_payload(record):
    return {key: record[key] for key in FIELDS if key in record}


def quantity_text(record):
    if not record.get("quantity_review"):
        return ""
    return (
        "Source quantity contract (not a combined procedure):\n"
        + json.dumps(quantity_payload(record), ensure_ascii=False)
        + "\nSelect ONE protocol variant. Keep its stocks, fresh aliquots and transfers separate. "
        "Do not infer doses, convert drops to mL, equate vessel capacity with fill, or substitute a range midpoint. "
        "Actual laboratory waiting/heating times are not generated clip durations."
    )


def select_protocol(record, variant_id=None):
    """Return steps only for a selected protocol; never concatenate alternatives."""
    variants=record.get("protocol_variants", [])
    if not variants:
        if variant_id:
            raise ValueError(f"{record['experiment_id']} has no quantity protocol variants")
        return record.get("procedure_steps", [])
    chosen=variant_id or record.get("selected_protocol_variant")
    if chosen is None:
        return []
    match=next((v for v in variants if v["variant_id"]==chosen),None)
    if match is None:
        raise ValueError(f"Unknown protocol {chosen!r} for {record['experiment_id']}")
    return match["procedure_steps"]
