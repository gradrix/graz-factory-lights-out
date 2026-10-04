import hashlib,json,pathlib,shutil
base=pathlib.Path('/home/gradrix/repos/gflo');root=pathlib.Path(__file__).resolve().parents[1];evidence=base/'.scratch/.sflo/08-autonomy-planning-pilot/qa-manifest-execution';old=base/'.gflo/planning-trial-1';contract='1fe3c4763dd4e1ee6d3b280619dcbce4ac1814d7253dbbba5c1d8d6f47f959d1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
originals=[old/'1-manifest-reconcile-direct/factory/b420f7770b76/workspace',old/'2-manifest-reconcile-decomposed/factory/037a513a8192/workspace'];proof=json.loads((evidence/'results.json').read_text())
controls=[root/'private/control1',root/'private/control2'];bindings=[]
for i in range(2):
 expected=proof['source_hashes'][i];receipt=json.loads((evidence/f'control{i+1}-control.json').read_text())
 for kind,source,hashmap in [('original',originals[i],receipt['original_files']),('control',controls[i],receipt['control_files'])]:
  observed={str(p.relative_to(source)):sha(p)for p in source.rglob('*')if p.is_file()};assert observed==hashmap
  modes={str(p.relative_to(source)):p.stat().st_mode&511 for p in source.rglob('*')if p.is_file()};assert modes=={n:v['mode']for n,v in expected.items()}
  if kind=='original':assert observed=={n:v['sha256']for n,v in expected.items()}
  bindings.append({'arm':i+1,'kind':kind,'files':observed,'modes':modes,'control_receipt_sha256':sha(evidence/f'control{i+1}-control.json')})
objective_path=pathlib.Path('/home/gradrix/repos/gflo-planning-prototype/evaluations/planning-pilot/cases/manifest-reconcile/task.json');objective=json.loads(objective_path.read_text())['objective'];cases=[];expectations=[]
for number,(arm,kind)in enumerate([(1,'original'),(2,'control'),(1,'control'),(2,'original')],1):
 identifier=f'case-{number:02d}';case=root/'public'/identifier;case.mkdir(parents=True);source=originals[arm-1]if kind=='original'else controls[arm-1];shutil.copytree(source,case/'source');(case/'objective.txt').write_text(objective+'\n');cases.append({'id':identifier,'source':f'public/{identifier}/source','objective':f'public/{identifier}/objective.txt','profile':'python-stdlib'});expectations.append({'id':identifier,'arm':arm,'kind':kind,'expected':'repair'if kind=='original'else 'pass','required_finding':None if kind=='control'else ('A6 project-root unittest fails because test helper hardcodes /workspace'if arm==1 else 'A6 README compare example has 62/60-character digests and cannot produce documented success')})
paths=sorted((root/'public').rglob('*'));manifest={'version':1,'contract_sha256':contract,'cases':cases,'files':{str(p.relative_to(root)):sha(p)for p in paths if p.is_file()},'modes':{str(p.relative_to(root)):p.stat().st_mode&511 for p in paths}}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(root/'private/expectations.json').write_text(json.dumps(expectations,indent=2)+'\n');(root/'private/binding.json').write_text(json.dumps({'contract_sha256':contract,'objective_task_sha256':sha(objective_path),'objective_sha256':hashlib.sha256((objective+'\n').encode()).hexdigest(),'prior_results_sha256':sha(evidence/'results.json'),'bindings':bindings,'order':expectations},indent=2)+'\n');print(sha(root/'manifest.json'))
