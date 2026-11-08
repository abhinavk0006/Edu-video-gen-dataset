# Generated reference pilots

Three draft visual trials are packaged with exact image hashes, generation prompts,
source-step snapshots/hashes, starting states and rendering excerpts in
`assets/reference_pilots/manifest.json`. Canonical records link them through
`reference_pilot_ids` and `image_assets`. Source procedures and quantities remain
unchanged. Generated images do not measure volume or validate chemistry.

| Pilot ID | Source protocol | What it shows |
|---|---|---|
| chloride_confirmation | chem_12_301 / chloride_silver | Prepared aliquot, then source steps 2-4 on one tube; exact reagent doses unresolved |
| thiosulphate_cross | chem_12_901 / hcl_1ml | Prepared aliquot, atomic delivery/swirl/observation adaptation; no generated rate measurement or forced two-second endpoint |
| starch_heating_excerpt | chem_12_801 / starch | Short excerpt of the ongoing source step-3 heating/stirring hold; not completion of ten minutes |

The pipeline's `load_reference_pilot` rejects missing/changed images and changed
source steps. References need independent scientific review before instructional
acceptance. The AI asset license/attribution review is also pending; `needs_review`
is not a statement of approved distribution rights.

Select the pilot ID in `Wan22_Kaggle_Continuous_State_Styled_Cards.ipynb`. Images
are loaded from the pinned dataset clone, with no separate Kaggle upload.
Reference creation used the built-in image-generation tool; exact prompts are in
`assets/reference_pilots/generation_prompts.json`.
