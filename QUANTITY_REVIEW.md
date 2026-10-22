# NCERT quantity enrichment - 22 October 2026

## What changed

All 100 catalogue records have a quantity-coverage assessment. The eleven
user-supplied NCERT XII chemistry units support changes to 23 chemistry
records, represented by 115 protocol variants. Nineteen records have their
selected source procedures transcribed; four aggregate records (salt analysis,
functional groups, food tests and colloids) have partial branch coverage.
"Transcribed" describes this data pass, not teacher approval or a certificate
that every dose is numerically complete. Records retain `source_review`.

The other 77 records retain their original procedure quantities: 75 are outside
these manuals, one is only cross-referenced and one has a related diagnostic
test rather than the matching preparative procedure. Physics is not covered.

The machine-readable inventory is `data/quantity_coverage_audit.json`.
`data/quantity_source_manifest.json` identifies the 11 local source files by
SHA-256, PDF page count and official source URL. Evidence uses **1-based PDF
pages**, not the printed page number. PDFs are not redistributed here.

## Quantity semantics

Each selected protocol contains `procedure_steps`, each with `quantities`,
`source_evidence`, `sample_id` and `reaction_scope`. Quantities distinguish:

- Fixed additions from approximate amounts and ranges. No range midpoint is chosen.
- Stock preparation from an aliquot transferred into the reaction vessel.
- Final solution volume from solvent volume added. Making up to 250 mL does
  not mean adding 250 mL water.
- Apparatus capacity from liquid volume and safe working volume.
- Ratios and relative portions from absolute volumes.
- Endpoint-controlled and qualitative additions from documented numerical doses.
- Laboratory process conditions from proposed video clip durations.

Unstated quantities use `qualifier: not_specified` with **no numeric value**.
"Few drops" is not silently converted to a count; drops are never converted to
mL without a separate calibration. No density, missing concentration, safe fill
limit or physical volume-additivity assumption is manufactured.

## Scientific distinctions relevant to the video pipeline

- Clear dissolved solutions, colloidal sols, precipitates and emulsions have
  different appearances; white is not a universal intermediate state.
- Homogeneous mixing can affect the whole contents. Brown-ring tests, solvent
  extraction, Molisch rings and surface-deposited silver deliberately require
  interfaces, layers or localised effects. A universal whole-liquid rule is wrong.
- Kinetics trials use fresh samples. Alternative tests and separate aliquots
  must not be concatenated into one accumulating tube.
- Observations are conditional on the analyte. An unknown salt or food sample
  is not assumed to give every positive test.
- Some source endpoints are nonvisual or historical hazardous methods. Those
  branches remain under review; an odour description is not an instruction to
  depict inhalation or to invent a colour change.

### Chloride example

`chem_12_301 / chloride_silver` records the source's 1 mL carbonate-extract
aliquot and the water-extract alternative. Nitric acid, silver nitrate and
ammonium hydroxide amounts/concentrations are not all stated. They stay unset.
The clear original solution, curdy white AgCl and subsequent dissolution are
distinct states. No universal salt mass, 20 mL starting solution, extra reagent
volume or test-tube capacity has been borrowed from another branch or from the
MgSO4 specimen record.

### Source conflicts retained for review

| Record | Source issue | Current treatment |
| --- | --- | --- |
| chem_12_205 | Catalogue said 0.05 M oxalic acid; lelm106 PDF p3 specifies 0.1 M | Title/procedure corrected to 0.1 M; old title retained in review metadata |
| chem_12_1101 | lelm104 PDF p3 materials list starts CuSO4 at 0.25 M; procedure and table use 0.2 M | Procedure/table value retained; discrepancy documented |
| chem_12_605 | lelm110 PDF p5 materials list gives 1.5 mL HNO3; numbered procedure gives 1.0 mL | Numbered procedure retained; discrepancy documented |
| chem_12_601 | lelm109 introduction mentions 2-3 mL acid generically, but scaled procedures specify about 0.4/0.5 mL | Step-specific scaled quantities retained |
| chem_12_1001 | Materials inventory includes 2 g; procedure uses an actually weighed W1 | No fixed 2 g experimental dose imposed |
| chem_12_201 | Oxalic-acid preparation points to the missing Class XI unit | No preparation mass or batch volume inferred |
| chem_12_607 | Supplied functional-group unit contains iodoform tests, not this preparation | Related tests linked; preparative record not rescaled |

## Choosing a protocol

`protocol_variants` are alternatives or independent controlled trials, not one
long procedure. `selected_protocol_variant` is null for multi-variant entries.
The prompt builder emits no video steps for an unselected multi-variant entry
and reports `planning_blocked`. Single-variant entries select that protocol.

```powershell
python scripts/build_rag_prompt_bundle.py "Detect one cation and one anion in a salt" --top-k 1 --protocol chem_12_301=chloride_silver --output exports/chloride_quantity_prompt_bundle.json
```

Selection is keyed by experiment ID so it cannot accidentally apply the same
variant name to unrelated retrieval results. Explicit selections pin the requested
record; the bundle labels their score as an explicit selection, not a measured
TF-IDF similarity. Search uses concise scientific terms while full quantity
evidence is retained for planning. A chosen protocol can still need
scientific review, preceding group separation, image preparation, dose approval
and clip splitting. Source quantities are passed as structured fields and text;
they do not claim that generated frames were measured or chemically verified.

The dataset does not automatically translate every range or endpoint into the
pipeline's numeric `liquid_state` budget. That translation requires resolving
the missing facts. A notebook that hard-codes clip definitions must be updated
to consume this selected protocol before it benefits from these fields.

## Rebuilding

```powershell
python scripts/apply_ncert_quantities.py --source-dir "C:\Users\Abhinav Krishna\Downloads"
python scripts/build_exports.py
python scripts/build_dataset_directory.py
python scripts/build_video_inputs.py
python scripts/build_rag_index.py
```

The per-file builder updates known generated JSON paths in place and preserves
images/unrelated files. It does not recursively delete the dataset directory.
Legacy procedure/material/scene/goal fields preserve the previous catalogue
content for comparison and are not the selected executable protocol.

This pass rebuilt data artifacts and checked Python syntax. No unit tests or
GPU video generation were run. Scientific acceptance and video-level
consistency remain pending.

## Record coverage

The following inventory is generated from the canonical coverage audit.

| Record | Experiment | Coverage | Variants |
| --- | --- | --- | --- |
| chem_8_001 | Testing Solubility of Common Substances | not_covered | 0 |
| chem_8_002 | Separating a Sand and Salt Mixture | not_covered | 0 |
| chem_9_001 | Diffusion of an Ink Drop in Water | not_covered | 0 |
| chem_9_002 | Law of Conservation of Mass | not_covered | 0 |
| chem_10_001 | Testing Acids and Bases with Indicators | not_covered | 0 |
| chem_10_002 | Reaction of Iron Nails with Copper Sulphate | not_covered | 0 |
| chem_11_001 | Preparation of a Standard Solution | not_covered | 0 |
| chem_11_002 | Effect of Concentration on an Equilibrium | not_covered | 0 |
| chem_12_101 | Determine the boiling point of an organic compound | not_covered | 0 |
| chem_12_102 | Determine the melting point of an organic compound | not_covered | 0 |
| chem_12_103 | Purify a given compound by crystallisation | not_covered | 0 |
| chem_12_201 | Prepare a standard solution of 0.1 M oxalic acid | cross_reference_only | 0 |
| chem_12_202 | Determine the strength of sodium hydroxide using standard oxalic acid | not_covered | 0 |
| chem_12_203 | Prepare a standard solution of 0.05 M sodium carbonate | not_covered | 0 |
| chem_12_204 | Determine the strength of hydrochloric acid using standard sodium carbonate | not_covered | 0 |
| chem_12_205 | Determine the molarity of potassium permanganate using 0.1 M oxalic acid | transcribed | 1 |
| chem_12_206 | Determine the molarity of potassium permanganate using Mohr's salt | transcribed | 1 |
| chem_12_301 | Detect one cation and one anion in a salt | partial | 36 |
| chem_12_401 | Detect extra elements in an organic compound | not_covered | 0 |
| chem_12_402 | Identify one functional group in an organic compound | partial | 19 |
| chem_12_403 | Characterise carbohydrates, fats, and proteins in food | partial | 14 |
| chem_12_501 | Separate pigments from leaf or flower extracts by paper chromatography and determine Rf values | transcribed | 2 |
| chem_12_502 | Separate lead and cadmium ions in an inorganic mixture by paper chromatography | transcribed | 1 |
| chem_12_601 | Prepare potash alum and Mohr's salt double salts | transcribed | 2 |
| chem_12_602 | Prepare potassium trioxalatoferrate(III) | transcribed | 1 |
| chem_12_603 | Prepare acetanilide | transcribed | 3 |
| chem_12_604 | Prepare dibenzalacetone | transcribed | 1 |
| chem_12_605 | Prepare p-nitroacetanilide | transcribed | 1 |
| chem_12_606 | Prepare phenyl-azo-beta-naphthol | transcribed | 1 |
| chem_12_607 | Prepare iodoform | related_test_only | 0 |
| chem_12_701 | Study pH change by common-ion effect in weak acids and bases | not_covered | 0 |
| chem_12_702 | Study equilibrium shifts caused by ion concentration or temperature | not_covered | 0 |
| chem_12_801 | Prepare lyophilic and lyophobic sols | partial | 6 |
| chem_12_802 | Purify a prepared sol by dialysis | transcribed | 1 |
| chem_12_803 | Study the role of emulsifying agents in stabilising oil emulsions | transcribed | 1 |
| chem_12_901 | Study concentration effects on sodium thiosulphate and hydrochloric acid reaction rate | transcribed | 5 |
| chem_12_902 | Study temperature effects on sodium thiosulphate and hydrochloric acid reaction rate | transcribed | 5 |
| chem_12_903 | Study iodide and hydrogen peroxide clock reaction at different concentrations | transcribed | 3 |
| chem_12_904 | Study potassium iodate and sodium sulphite clock reaction | transcribed | 4 |
| chem_12_1001 | Determine enthalpy of solution of potassium nitrate | transcribed | 1 |
| chem_12_1002 | Determine enthalpy of neutralisation of hydrochloric acid and sodium hydroxide | transcribed | 1 |
| chem_12_1101 | Study cell potential of Zn|Zn2+||Cu2+|Cu as electrolyte concentration changes | transcribed | 5 |
| phy_11_001 | Use of Vernier Callipers to measure dimensions, volume, and density | not_covered | 0 |
| phy_11_002 | Use of screw gauge to measure wire diameter, sheet thickness, and lamina volume | not_covered | 0 |
| phy_11_003 | Determine the radius of curvature of a spherical surface by a spherometer | not_covered | 0 |
| phy_11_004 | Determine masses of two objects using a beam balance | not_covered | 0 |
| phy_11_005 | Measure the weight of a body using the parallelogram law of vector addition | not_covered | 0 |
| phy_11_006 | Plot L-T and L-T squared graphs for a simple pendulum and find effective length of a seconds pendulum | not_covered | 0 |
| phy_11_007 | Study limiting friction versus normal reaction and determine coefficient of friction | not_covered | 0 |
| phy_11_008 | Find the downward force on a roller along an inclined plane and relate it to sin theta | not_covered | 0 |
| phy_11_009 | Find the force constant and effective mass of a helical spring using oscillations | not_covered | 0 |
| phy_11_010 | Study volume versus pressure for air at constant temperature | not_covered | 0 |
| phy_11_011 | Determine coefficient of viscosity of a liquid using terminal velocity | not_covered | 0 |
| phy_11_012 | Study temperature of a hot body versus time using a cooling curve | not_covered | 0 |
| phy_11_013 | Study frequency and length, and length and tension, of a wire using a sonometer | not_covered | 0 |
| phy_11_014 | Determine speed of sound in air using a resonance tube | not_covered | 0 |
| phy_11_015 | Determine specific heat capacity of a solid and liquid by the method of mixtures | not_covered | 0 |
| phy_11_101 | Make paper scales of least count 0.2 cm and 0.5 cm and measure length | not_covered | 0 |
| phy_11_102 | Determine mass of a body using a metre scale and the principle of moments | not_covered | 0 |
| phy_11_103 | Plot a graph from data using a proper scale and show precision error bars | not_covered | 0 |
| phy_11_104 | Measure rolling friction force for a roller on a horizontal plane | not_covered | 0 |
| phy_11_105 | Study range of a water jet versus angle of projection | not_covered | 0 |
| phy_11_106 | Study conservation of energy of a ball rolling down an inclined plane | not_covered | 0 |
| phy_11_107 | Study dissipation of energy of a simple pendulum with time | not_covered | 0 |
| phy_11_108 | Observe change of state and plot a cooling curve for molten wax | not_covered | 0 |
| phy_11_109 | Observe and explain heating of a bi-metallic strip | not_covered | 0 |
| phy_11_110 | Study heating effect on liquid level in a container | not_covered | 0 |
| phy_11_111 | Study detergent effect on water surface tension using capillary rise | not_covered | 0 |
| phy_11_112 | Study load effect on depression of a clamped metre scale | not_covered | 0 |
| phy_12_001 | Determine resistance per unit length of a wire from a potential difference-current graph | not_covered | 0 |
| phy_12_002 | Determine wire resistance and resistivity using a metre bridge | not_covered | 0 |
| phy_12_003 | Verify series and parallel laws of combination of resistances using a metre bridge | not_covered | 0 |
| phy_12_004 | Compare emf of Daniel and Leclanche primary cells using a potentiometer | not_covered | 0 |
| phy_12_005 | Determine internal resistance of a primary cell using a potentiometer | not_covered | 0 |
| phy_12_006 | Determine galvanometer resistance by half-deflection and its figure of merit | not_covered | 0 |
| phy_12_007 | Convert a galvanometer into an ammeter and voltmeter and verify the ranges | not_covered | 0 |
| phy_12_008 | Determine frequency of alternating current using a sonometer | not_covered | 0 |
| phy_12_009 | Find focal length of a concave mirror from object and image distances | not_covered | 0 |
| phy_12_010 | Find focal length of a convex lens using u-v or reciprocal graphs | not_covered | 0 |
| phy_12_011 | Find focal length of a convex mirror using a convex lens | not_covered | 0 |
| phy_12_012 | Find focal length of a concave lens with a convex lens | not_covered | 0 |
| phy_12_013 | Determine minimum deviation angle of a glass prism from an incidence-deviation graph | not_covered | 0 |
| phy_12_014 | Determine refractive index of water using a concave mirror, convex lens, and plane mirror | not_covered | 0 |
| phy_12_015 | Draw forward and reverse I-V characteristics of a p-n junction | not_covered | 0 |
| phy_12_016 | Draw a Zener diode characteristic curve and determine reverse breakdown voltage | not_covered | 0 |
| phy_12_017 | Study common-emitter transistor characteristics and determine current and voltage gains | not_covered | 0 |
| phy_12_101 | Assemble components of a given electrical circuit | not_covered | 0 |
| phy_12_102 | Correct an incorrectly connected circuit and draw the corrected diagram | not_covered | 0 |
| phy_12_103 | Measure resistance and impedance of an inductor with or without an iron core | not_covered | 0 |
| phy_12_104 | Use a multimeter to measure resistance, voltage, current, and continuity | not_covered | 0 |
| phy_12_105 | Assemble a household circuit with bulbs, switches, fuse, and power source | not_covered | 0 |
| phy_12_106 | Study potential drop versus length for a steady-current wire | not_covered | 0 |
| phy_12_107 | Study light intensity effect on an LDR by varying source distance | not_covered | 0 |
| phy_12_108 | Identify a diode, LED, transistor, IC, resistor, and capacitor from a mixed set | not_covered | 0 |
| phy_12_109 | Check a diode, distinguish npn and pnp transistors, and identify transistor terminals | not_covered | 0 |
| phy_12_110 | Observe refraction and lateral deviation through a glass slab | not_covered | 0 |
| phy_12_111 | Observe polarisation using two polaroids | not_covered | 0 |
| phy_12_112 | Observe diffraction of light through a thin slit | not_covered | 0 |
| phy_12_113 | Study image nature and size for a convex lens and concave mirror using candle and screen | not_covered | 0 |
| phy_12_114 | Determine focal length of two lenses in contact | not_covered | 0 |
