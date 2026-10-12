#!/usr/bin/env python3
"""Replay the sole randomized selected HumanEval test with a fixed seed."""
import pathlib,json,re,subprocess
root=pathlib.Path(__file__).parent
task=next(x for x in map(json.loads,(root/'humaneval.jsonl').read_text().splitlines()) if x['task_id']=='HumanEval/53')
results=[]
for path in sorted((root/'results').glob('*.jsonl')):
 for row in map(json.loads,path.read_text().splitlines()):
  if row.get('name')!='HumanEval/53':continue
  code=row.get('text','');m=re.search(r'```(?:python)?\s*\n(.*?)```',code,re.S);code=m.group(1) if m else code
  source=code+'\nimport random\nrandom.seed(5090)\n'+task['test']+'\ncheck('+task['entry_point']+')\n'
  r=subprocess.run(['docker','run','--rm','-i','--network','none','--memory','128m','--cpus','1','--pids-limit','32','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca','python','-I','-'],input=source,text=True,capture_output=True,timeout=20)
  results.append({'file':path.name,'task':row['name'],'original_passed':row['passed'],'seeded_passed':r.returncode==0,'output':(r.stdout+r.stderr)[-1000:]})
(root/'random-grading-audit.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
raise SystemExit(0 if all(x['original_passed']==x['seeded_passed'] for x in results) else 1)
