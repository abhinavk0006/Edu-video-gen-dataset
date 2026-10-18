# Source-grounded scientific contracts

Procedure steps can now include `science_spec`, `visibility_targets`,
`handoff_requirements`, `render_mode`, `circuit` and `diagram_timeline`.
The experiment JSON schema documents optional structures. Existing data remains
valid; adding fields does not certify an experiment.

`scripts/science_contract.py` transcribes explicit action/observation text into
draft requirements when no contract exists. It sets `source_reviewed: false`,
does not infer apparatus IDs, hidden reaction states or exact amounts, and does
not invent temporal relationships. A reviewer must validate source pages,
preconditions, invariant objects and event ordering.

The bundle builder carries the contract into the pipeline's metadata. The
pipeline keeps expected requirements separate from observed timestamped review
evidence. Both source provenance and footage review are needed for acceptance.
See the pipeline repository's `SCIENCE_RESEARCH.md` for evidence and study tools.

Textbook-style physics reference diagrams should encode components, terminals
and connections explicitly rather than use a generic lab-bench description.
Reviewed graph templates and deterministic rendering are supported by the new
pipeline circuit backend; the existing physics corpus has not been automatically
converted or certified against NCERT figures in this change.
