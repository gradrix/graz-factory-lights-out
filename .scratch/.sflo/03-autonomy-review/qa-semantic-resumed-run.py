import pathlib, subprocess, json, hashlib
root=pathlib.Path.cwd(); out=root/'.scratch/.sflo/03-autonomy-review'
image=subprocess.check_output(['docker','image','inspect','python:3.12-slim','--format','{{.Id}}'],text=True).strip()
runs={'05':'3a580376311a','06':'df03c8b4fc28','07':'fb1fb7b64726','08':'751bc03d4c4b','09':'fa94c69430ad','10':'ef27abbc21eb','11':'c38088d51d73','12':'aefc008cb097','02-repair':'repair','03':'3c48308dd1cc'}
results=[]
for task,run in runs.items():
 workspace=root/('.gflo/project-test-repair-result/workspace' if run=='repair' else f'.gflo/semantic-b/{run}/workspace')
 fixture=next((root/'evaluations/coding-b/tasks').glob(task[:2]+'-*'))
 hashes={str(p.relative_to(workspace)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(workspace.rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
 identity=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
 base=['docker','run','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,noexec,nosuid,size=16m','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(workspace)+':/workspace:ro','-v',str(fixture/'acceptance')+':/acceptance:ro','-w','/workspace',image]
 checks={}
 for name,args in [('acceptance',['python','-B','-I','/acceptance/check.py']),('generated',['python','-B','-m','unittest','discover','-s','tests','-v'])]:
  p=subprocess.run(base+args,capture_output=True,text=True,timeout=40); checks[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 if task=='03':
  code="import resource;resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024));from api import dispatch; p={'action':'schedule','now':0,'attempt':10**30,'base':1,'cap':10,'max_attempts':10**30+1,'outcome':'transient'}; control={'retry':True,'at':10,'delay':10}; assert max(min(p['cap'],p['base'] << min(p['attempt']-1,p['cap'].bit_length())),0)==10; print('control passes',flush=True); print(dispatch(p))"
  p=subprocess.run(base+['python','-B','-c',code],capture_output=True,text=True,timeout=15);checks['extreme']={'command':code,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 if task=='11':
  code="from api import dispatch\ndef run(a,b):\n return dispatch({'action':'ingest','watermarks':{},'events':[{'source':'x','seq':1,'data':a},{'source':'x','seq':1,'data':b}]})\nassert len(run({'a':[1]}, {'a':[1.0]})['released'])==1\nfor a,b in [(True,1),({'a':[False]},{'a':[0]}),(10**20+1,float(10**20))]:\n try: run(a,b)\n except ValueError: pass\n else: raise AssertionError((a,b))\nr=dispatch({'action':'ingest','watermarks':{},'events':[{'source':'x','seq':10**30,'data':None}]});assert r['watermarks']=={'x':0} and len(r['pending'])==1\nprint('equality and sparse sequence probes pass')"
  p=subprocess.run(base+['python','-B','-c',code],capture_output=True,text=True,timeout=15);checks['supplemental']={'command':code,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 results.append({'task':task,'run':run,'identity':identity,'file_hashes':hashes,'checks':checks})
 print(task,identity,{k:v['exit'] for k,v in checks.items()},flush=True)
(out/'qa-semantic-resumed-results.json').write_text(json.dumps({'image':image,'sandbox':base[:19],'results':results},indent=2)+'\n')
