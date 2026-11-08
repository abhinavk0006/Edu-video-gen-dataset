"""Register one inspected reference and bind its exact source protocol. No dose invention."""
import argparse,datetime,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def dump(path,value):
 path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def register(spec,image_source):
 pid=spec.pop('pilot_id'); prompt=spec.pop('prompt',None)
 path=ROOT/'data/chemistry_experiments.json';data=json.loads(path.read_text(encoding='utf-8'))
 record=next(r for r in data['experiments'] if r['experiment_id']==spec['experiment_id'])
 variant=next(v for v in record['protocol_variants'] if v['variant_id']==spec['protocol_variant'])
 steps={s['step_id']:s for s in variant['procedure_steps']}
 for clip in spec['clips']:
  source=steps[clip['source_step_id']]
  allowed={q['reagent'] for q in source['quantities']}
  if not set(clip.get('quantity_reagents',[]))<=allowed: raise ValueError('Unknown source reagent')
 registry_path=ROOT/'assets/reference_pilots/manifest.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
 if pid in registry['pilots']: raise ValueError('Existing pilot: use a new versioned ID')
 if image_source:
  relative='assets/reference_pilots/'+pid+'.png';dest=ROOT/relative
  if dest.exists(): raise ValueError('Asset already exists')
  shutil.copyfile(image_source,dest)
 else:
  relative=spec.pop('reuse_image_path');dest=ROOT/relative
  if not spec.get('reuse_rationale'): raise ValueError('Reuse needs a starting-state compatibility rationale')
 if not dest.is_file(): raise ValueError('Missing image')
 from PIL import Image
 with Image.open(dest) as image: image.verify()
 spec['source_step_hashes']={str(sid):hashlib.sha256(json.dumps(s,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for sid,s in steps.items()}
 spec['source_step_snapshots']=list(steps.values())
 spec['image']={'path':relative,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'origin':'built_in_imagegen','created':datetime.date.today().isoformat(),'scientific_review_status':'pending','volume_measured':False,'prompt_file':'assets/reference_pilots/generation_prompts.json','prompt_key':pid if prompt else spec.pop('reuse_prompt_key'),'visual_checks':'Assistant inspected count, apparatus, visibility and requested initial appearance. Independent scientific review pending.'}
 spec['review_status']='draft';spec['scientifically_verified']=False
 registry['pilots'][pid]=spec;dump(registry_path,registry)
 if prompt:
  p=ROOT/'assets/reference_pilots/generation_prompts.json';prompts=json.loads(p.read_text(encoding='utf-8'));prompts[pid]=prompt;dump(p,prompts)
 record.setdefault('reference_pilot_ids',[]).append(pid)
 record['image_assets'].append({'image_asset_id':pid+'_generated_reference','role':'scene_reference','url':relative,'license_status':'needs_review','attribution':f'AI-generated draft reference for {pid}; see source-bound pilot manifest. Scientific review pending.'})
 dump(path,data)
 print('Registered',pid,relative)
 return pid
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('spec',type=Path);parser.add_argument('--image',type=Path);args=parser.parse_args()
 register(json.loads(args.spec.read_text(encoding='utf-8-sig')),args.image)
