import ast,hashlib,json,pathlib,subprocess,tempfile
R=pathlib.Path('.gflo/coding-qualification-c').resolve(); E=pathlib.Path('.scratch/.sflo/03-autonomy-review').resolve()
m=json.loads((R/'manifest.json').read_text());assert hashlib.sha256((R/'manifest.json').read_bytes()).hexdigest()=='4aeb6fd0c2e88c0ad393d1a659eb062ae321f0db1a04dec80adb84ff880ef11f'
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in m['sha256'].items())
print('manifest verified',len(m['sha256']),flush=True)
image='sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578';results=[]
def run(n,kind,mutate=lambda files:None):
 d=next((R/'tasks').glob(n+'-*'));files=json.loads((R/'private'/f'{n}-reference.json').read_text());mutate(files)
 with tempfile.TemporaryDirectory(prefix='cohort-c-qa-') as tmp:
  w=pathlib.Path(tmp);w.chmod(0o755)
  for name,c in files.items():(w/name).write_text(c)
  p=subprocess.run(['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--pids-limit','128','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-v',f'{d}/acceptance:/acceptance:ro','-w','/workspace',image,'python','-B','-I','/acceptance/check.py'],capture_output=True,text=True,timeout=60)
  result=dict(task=d.name,kind=kind,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr);results.append(result);print(d.name,kind,p.returncode,flush=True)
def alter(text):
 def apply(f):f['domain.py']=text
 return apply
for n in ['01','07','08','06']:run(n,'reference')
run('01','float-quota',lambda f:f.update({'domain.py':f['domain.py'].replace('a=[s*x//t for x in w]','a=[int(s*x/t) for x in w]').replace('-(s*w[i]%t)','-(s*w[i]/t-int(s*w[i]/t))')}))
run('07','persistent-clamp',lambda f:f.update({'domain.py':f['domain.py'].replace('m+=1',"p['day']=d.day\n  m+=1")}))
run('08','greedy',alter("def identity(p):return p['value']\ndef feature(p):\n used=set()\n for choices in p['choices']:\n  for r in choices:\n   if r not in used:used.add(r);break\n return len(used)\n"))
run('06','integer-instead-of-boolean',lambda f:f.update({'api.py':f['api.py'].replace('return domain.feature(payload)',"return int(domain.feature(payload)) if action=='check' else domain.feature(payload)")}))
run('08','missing-tests',lambda f:f.pop('test_behavior.py'))
run('08','failing-tests',lambda f:f.update({'test_behavior.py':f['test_behavior.py'].replace('self.assertEqual(', 'self.fail();self.assertEqual(')}))
run('08','missing-docs',lambda f:f.update({'README.md':'# Old README'}))
(E/'qa-cohort-c-probe.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['exit_code']==0 for r in results if r['kind']=='reference')
assert all(r['exit_code']!=0 for r in results if r['kind'] not in ['reference','integer-instead-of-boolean'])
assert next(r for r in results if r['kind']=='integer-instead-of-boolean')['exit_code']==0
