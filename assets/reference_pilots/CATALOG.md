# Source-linked image pilot catalog

23 pilot configurations use 18 distinct reference images. All are drafts pending independent scientific review and real GPU generation tests.

Use the persistent-worker Continuous State Styled Cards notebook. Set `PILOT_ID` in its first configuration cell, then run setup and inspect the starting reference, source scope, material plan and cards before GPU generation. No separate image upload is needed.

Start tomorrow with `carboxyl_litmus`, `salt_water_delivery` and `starch_iodine` (one shot each), then test the `chloride_confirmation` and `sulphate_confirmation` handoffs. Compare `thiosulphate_cross`, `thiosulphate_cross_2ml` and `thiosulphate_cross_4ml` as independent fresh trials. This is a qualitative generation comparison, not measured reaction kinetics.

| PILOT_ID | Source record / protocol | Shots | Reference |
|---|---|---:|---|
| `chloride_confirmation` | chem_12_301 / chloride_silver | 3 | [image](chloride_prepared_aliquot.png) |
| `thiosulphate_cross` | chem_12_901 / hcl_1ml | 3 | [image](thiosulphate_clear_cross.png) |
| `starch_heating_excerpt` | chem_12_801 / starch | 1 | [image](starch_sol_heating.png) |
| `starch_iodine` | chem_12_403 / starch_iodine | 1 | [image](starch_iodine.png) |
| `gum_sol` | chem_12_801 / gum | 2 | [image](gum_sol.png) |
| `oil_soap_delivery` | chem_12_803 / oil_comparison | 1 | [image](oil_soap_delivery.png) |
| `biuret_copper_delivery` | chem_12_403 / biuret | 1 | [image](biuret_copper_delivery.png) |
| `mohr_titration_excerpt` | chem_12_206 / mohr_0p05m | 2 | [image](mohr_titration_excerpt.png) |
| `salt_water_delivery` | chem_12_301 / original_solution | 1 | [image](salt_water_delivery.png) |
| `nitrate_calorimetry` | chem_12_1001 / potassium_nitrate | 2 | [image](nitrate_calorimetry.png) |
| `thiosulphate_cross_2ml` | chem_12_901 / hcl_2ml | 3 | [image](thiosulphate_clear_cross.png) |
| `thiosulphate_cross_4ml` | chem_12_901 / hcl_4ml | 3 | [image](thiosulphate_clear_cross.png) |
| `leaf_chromatography` | chem_12_501 / acetone | 1 | [image](leaf_chromatography.png) |
| `copper_ammonia` | chem_12_301 / cation_copper | 1 | [image](copper_ammonia.png) |
| `iron_thiocyanate` | chem_12_301 / cation_iron | 1 | [image](iron_thiocyanate.png) |
| `iron_ferrocyanide` | chem_12_301 / cation_iron | 1 | [image](iron_thiocyanate.png) |
| `alum_cooling_excerpt` | chem_12_601 / potash_alum | 1 | [image](alum_cooling_excerpt.png) |
| `albumin_dialysis` | chem_12_802 / dialysis | 1 | [image](albumin_dialysis.png) |
| `alum_crystal_washing` | chem_12_601 / potash_alum | 1 | [image](alum_crystal_washing.png) |
| `carboxyl_litmus` | chem_12_402 / carboxyl_litmus | 1 | [image](carboxyl_litmus.png) |
| `leaf_chromatography_chloroform` | chem_12_501 / chloroform | 1 | [image](leaf_chromatography.png) |
| `sulphate_confirmation` | chem_12_301 / sulphate | 2 | [image](chloride_prepared_aliquot.png) |
| `fehling_waterbath` | chem_12_403 / fehling | 1 | [image](fehling_waterbath.png) |

## Reuse decisions

Reuse requires a matching visible starting state: apparatus and capacity class, sample appearance/phase, fill geometry, tools, observation markers and action access. It does not establish chemical identity, mL, concentration, temperature or prior procedural history. Those remain separate protocol claims. Fresh trials have distinct sample tracks; later shots on one sample use generated final-frame handoffs.

- **thiosulphate_cross_2ml:** Identical visible pre-acid state: fresh 50 mL 0.1 M clear thiosulphate in the same 100 mL beaker geometry above a visible cross. Acid dose differs only after this image. This is a fresh independent trial, not the previous trial continued. Image does not verify concentration, volume or temperature.
- **thiosulphate_cross_4ml:** Identical visible pre-acid state: fresh 50 mL 0.1 M clear thiosulphate in the same 100 mL beaker geometry above a visible cross. Acid dose differs only after this image. This is a fresh independent trial, not the previous trial continued. Image does not verify concentration, volume or temperature.
- **iron_ferrocyanide:** The two confirmation tests begin with visually matching separate portions of the same prepared acidic ferric solution, before either reagent: one tube, pale-yellow transparent low fill and abundant headspace. Shared raster composition is not shared physical sample identity; each pilot has its own state track. Actual concentration and aliquot volume remain unverified.
- **leaf_chromatography_chloroform:** Same visible paper geometry, dried leaf spot above a shallow clear mobile phase and undeveloped upper paper. The alternative mobile-phase composition changes chemical identity and development behaviour, but no pre-development visible feature in this image. This is an independent preparation, not the acetone run continued; no shared Rf or timing is assumed.
- **sulphate_confirmation:** Same visible pre-reagent state: a fresh low-volume clear colourless 1 mL water-extract aliquot in one upright tube. This pilot assumes a colourless sulphate-positive extract, not the chloride sample's chemical identity or prior acidification. Separate pilot/sample track; no amount, concentration or positive result inferred from pixels.

## Scope and remaining review

These are source-linked excerpts, not complete validated experiment videos. Each manifest entry records omitted preparation, waiting and measurement stages. Minutes-long processes are not declared complete in two-second clips. Source snapshots retain the complete procedure even where an atomic clip selects only one reagent.

The notebook defaults to warn/observe modes for draft visual trials. Unspecified quantities remain unspecified. Strict acceptance requires source-backed material limits and scientific review. Never treat the generated reference as a volumetric calibration, positive identification or measured experimental result. Apparatus rendering choices need review against the source manual. Physics references remain pending the source manual.

Generation attempts retain the existing automatic technical/research benchmark capture. VBench inputs are only scored when its evaluator is available. Scientific accuracy and endpoint correctness remain pending review; a successful push or CPU check is not a benchmark result.

Images were made with the built-in image-generation tool. Exact prompts are in [generation_prompts.json](generation_prompts.json); procedure hashes, snapshots and independent sample definitions are in [manifest.json](manifest.json).
