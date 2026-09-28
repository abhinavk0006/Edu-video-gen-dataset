# NCERT Chemistry Experiment Dataset

A lightweight, source-traceable catalog of school Chemistry and Physics experiments and activities for Classes 8-12. This repository contains dataset assets only; it does not clone or depend on the video-generation project or download model weights.

## Repository layout

- `data/chemistry_experiments.json`: canonical source-of-truth records for Chemistry and Physics
- `data/class12_practicals_index.json`: Class 12 practical inventory transcribed from the supplied index image
- `schema/experiment.schema.json`: JSON Schema for validating records
- `exports/`: generated retrieval and prompt-ready files
- `dataset/`: per-experiment JSON files organized by subject and difficulty, plus `metadata.json`
- `scripts/validate_dataset.py`: standard-library validator
- `scripts/build_exports.py`: builds JSONL exports for RAG and prompt generation
- `scripts/build_rag_index.py`: builds the local TF-IDF retrieval index
- `scripts/query_rag.py`: searches the local retrieval index
- `scripts/build_rag_prompt_bundle.py`: retrieves experiments and creates grounded scene-step prompts
- `scripts/api_prompt_variation_test.py`: sends prompt variants to a video-generation API
- `requirements.txt`: dependencies for the local RAG index

## Data contract

Each experiment has a stable `experiment_id`, class and subject metadata, learning goal, materials, ordered procedure steps, visual scenes, source references, and image metadata. `source_status` distinguishes records that still need manual source verification from verified records.

The canonical file is deliberately more detailed than the current video pipeline input. The video pipeline should consume a derived export, not become the source of truth.

`Manual_01.pdf` is the authoritative Chemistry source for the current Class 12 records. `Physics_Laboratory_Manual_11-12_E.pdf` is the authoritative Physics source for the current Classes XI-XII inventory. The photographed Chemistry index is retained only as superseded provenance in `data/class12_practicals_index.json`; its page numbers and formulas do not control the canonical catalog.

## Quick start

From this directory, create and activate the repository-local environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Validate the dataset and rebuild its derived exports:

```powershell
python scripts/validate_dataset.py
python scripts/build_exports.py
python scripts/build_dataset_directory.py
```

The exporter creates:

- `exports/chemistry_experiments.jsonl`: one complete record per line
- `exports/rag_documents.jsonl`: one searchable text document per experiment
- `exports/prompt_inputs.jsonl`: compact inputs for generating scene/prompt bundles

To build the directory-form dataset requested by downstream tooling:

```powershell
python scripts/build_dataset_directory.py
```

This creates `dataset/physics/{easy,medium,hard}/`, `dataset/chemistry/{easy,medium,hard}/`, and `dataset/metadata.json`. The image folders contain placeholders only; each record points to the expected local image path until a real, license-reviewed image is added.

To build or refresh the local RAG index:

```powershell
python scripts/build_rag_index.py
python scripts/demo_rag.py
```

To retrieve an experiment and build prompts from its canonical scenes and procedure:

```powershell
python scripts/build_rag_prompt_bundle.py "ohm law" --top-k 1 --output exports/ohm_law_prompt_bundle.json
```

The bundle contains the retrieved experiment, source IDs, starting-image references, and one prompt per procedure step. Those prompts can be sent to the API harness directly:

```powershell
python scripts/api_prompt_variation_test.py --prompts-file exports/ohm_law_prompt_bundle.json --url http://localhost:8000/generate --json-output exports/ohm_law_api_results.json
```

To run prompt variations against the video-generation API:

```powershell
python scripts/api_prompt_variation_test.py --url http://localhost:8000/generate --json-output results.json
```

The API server must already be running at that URL. This repository contains the client harness, but does not yet contain a local video-generation server or model runner.

## Source and image policy

NCERT is the primary curriculum anchor. The initial catalog uses official NCERT textbook and laboratory-manual landing pages as references, with page-level citations to be filled during source verification. Image fields may contain placeholders until a real, license-compatible image is selected. Do not treat a placeholder as a usable image asset.

## Scope

The current seed contains Chemistry Classes 8-12 and the Physics Classes XI-XII experiments and activities listed in the supplied manual. Physics records are initially marked `source_review`; their titles and source provenance are manual-grounded, while exact page-level citations, apparatus quantities, and real image assets remain a follow-up enrichment pass.
