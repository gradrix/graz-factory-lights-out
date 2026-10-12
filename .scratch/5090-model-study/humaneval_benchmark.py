#!/usr/bin/env python3
"""One deterministic 32-task HumanEval subset; this is not an official leaderboard run."""
import argparse,sys,pathlib,json,random,re,subprocess,runpy,ast
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=18000);p.add_argument('--container',default='');p.add_argument('--label',default='canonical');p.add_argument('--llama',action='store_true');p.add_argument('--verify-only',action='store_true');p.add_argument('--thinking',action='store_true');p.add_argument('--ids',default='');a=p.parse_args()
root=pathlib.Path(__file__).parent
all_tasks=[json.loads(line) for line in (root/'humaneval.jsonl').read_text().splitlines()]
def stdlib_only(task):
 code=task['prompt']+task['canonical_solution']+'\n'+task['test']
 imports=[]
 for n in ast.walk(ast.parse(code)):
  if isinstance(n,ast.Import):imports += [x.name.split('.')[0] for x in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module:imports.append(n.module.split('.')[0])
 return all(m in sys.stdlib_module_names for m in imports)
pool=[t for t in all_tasks if stdlib_only(t)]
tasks=random.Random(5090).sample(pool,32)
(root/'humaneval-subset.json').write_text(json.dumps({'seed':5090,'pool_size':len(pool),'task_ids':[x['task_id'] for x in tasks],'excluded_nonstdlib':[x['task_id'] for x in all_tasks if not stdlib_only(x)]},indent=2))
if a.ids:tasks=[t for t in tasks if t['task_id'] in a.ids.split(',')]
def grade(code,task):
 container='heval-5090-'+task['task_id'].split('/')[-1]
 try:
  r=subprocess.run(['docker','run','--rm','--name',container,'-i','--network','none','--memory','128m','--cpus','1','--pids-limit','32','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca','python','-I','-'],input=code+'\nimport random\nrandom.seed(5090)\n'+task['test']+'\ncheck('+task['entry_point']+')\n',text=True,capture_output=True,timeout=20)
  return r.returncode==0,(r.stdout+r.stderr)[-2000:]
 except subprocess.TimeoutExpired:
  subprocess.run(['docker','rm','-f',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return False,'20-second sandbox deadline'
if a.verify_only:
 results=[]
 for task in tasks:
  ok,msg=grade(task['prompt']+task['canonical_solution'],task);results.append({'task_id':task['task_id'],'passed':ok,'output':msg});print(task['task_id'],ok,flush=True)
 (root/'humaneval-canonical-check.json').write_text(json.dumps(results,indent=2));raise SystemExit(0 if all(x['passed'] for x in results) else 1)
sys.argv=['benchmark.py','--port',str(a.port),'--container',a.container,'--label',a.label,'--out',str(root/'results')]+(['--llama'] if a.llama else [])
b=runpy.run_path(str(root/'benchmark.py'))
for task in tasks:
 prompt='Implement the following Python function exactly as specified. Return the complete Python module including required imports and the function signature. Return only code, with no explanation.\n\n'+task['prompt']
 settings={'max_tokens':1024}
 if a.thinking:settings.update(max_tokens=4096,reasoning_effort='medium',chat_template_kwargs={'enable_thinking':True,'reasoning_effort':'medium'})
 r=b['request'](task['task_id'],b['chat'](prompt),**settings)
 code=r.get('text','');m=re.search(r'```(?:python)?\s*\n(.*?)```',code,re.S);code=m.group(1) if m else code
 r['passed'],r['grade_output']=grade(code,task) if 'error' not in r else (False,'inference failed')
 r['dataset']=f'HumanEval original, stdlib subset seed5090, n={len(tasks)}, thinking={a.thinking}';b['save'](r)
