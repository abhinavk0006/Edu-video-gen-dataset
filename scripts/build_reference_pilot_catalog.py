"""Build the runnable pilot catalog from the source-bound reference registry."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 pilots=json.loads((ROOT/'assets/reference_pilots/manifest.json').read_text(encoding='utf-8'))['pilots']
 images={p['image']['path'] for p in pilots.values()}
 lines=['# Source-linked image pilot catalog','',f'{len(pilots)} pilot configurations use {len(images)} distinct reference images. All are drafts pending independent scientific review and real GPU generation tests.','',
 'Use the persistent-worker Continuous State Styled Cards notebook. Set `PILOT_ID` in its first configuration cell, then run setup and inspect the starting reference, source scope, material plan and cards before GPU generation. No separate image upload is needed.','',
 'Start tomorrow with `carboxyl_litmus`, `salt_water_delivery` and `starch_iodine` (one shot each), then test the `chloride_confirmation` and `sulphate_confirmation` handoffs. Compare `thiosulphate_cross`, `thiosulphate_cross_2ml` and `thiosulphate_cross_4ml` as independent fresh trials. This is a qualitative generation comparison, not measured reaction kinetics.','',
 '| PILOT_ID | Source record / protocol | Shots | Reference |','|---|---|---:|---|']
 for pid,p in pilots.items():
  lines.append(f"| `{pid}` | {p['experiment_id']} / {p['protocol_variant']} | {len(p['clips'])} | [image]({Path(p['image']['path']).name}) |")
 lines+=['','## Reuse decisions','',
 'Reuse requires a matching visible starting state: apparatus and capacity class, sample appearance/phase, fill geometry, tools, observation markers and action access. It does not establish chemical identity, mL, concentration, temperature or prior procedural history. Those remain separate protocol claims. Fresh trials have distinct sample tracks; later shots on one sample use generated final-frame handoffs.','']
 for pid,p in pilots.items():
  if 'reuse_rationale' in p: lines.append(f"- **{pid}:** {p['reuse_rationale']}")
 lines+=['','## Scope and remaining review','',
 'These are source-linked excerpts, not complete validated experiment videos. Each manifest entry records omitted preparation, waiting and measurement stages. Minutes-long processes are not declared complete in two-second clips. Source snapshots retain the complete procedure even where an atomic clip selects only one reagent.','',
 'The notebook defaults to warn/observe modes for draft visual trials. Unspecified quantities remain unspecified. Strict acceptance requires source-backed material limits and scientific review. Never treat the generated reference as a volumetric calibration, positive identification or measured experimental result. Apparatus rendering choices need review against the source manual. Physics references remain pending the source manual.','',
 'Generation attempts retain the existing automatic technical/research benchmark capture. VBench inputs are only scored when its evaluator is available. Scientific accuracy and endpoint correctness remain pending review; a successful push or CPU check is not a benchmark result.','',
 'Images were made with the built-in image-generation tool. Exact prompts are in [generation_prompts.json](generation_prompts.json); procedure hashes, snapshots and independent sample definitions are in [manifest.json](manifest.json).','']
 (ROOT/'assets/reference_pilots/CATALOG.md').write_text('\n'.join(lines),encoding='utf-8')
 print(len(pilots),'pilots',len(images),'images',len({p['experiment_id'] for p in pilots.values()}),'dataset records')
if __name__=='__main__':main()
