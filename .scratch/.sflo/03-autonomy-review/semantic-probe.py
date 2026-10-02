import pathlib,json,tempfile,subprocess,hashlib
root=pathlib.Path('/home/gradrix/repos/gflo'); fixture=root/'.gflo/review-qualification-prepared';out=root/'.scratch/.sflo/03-autonomy-review';results=[]
for p in sorted((fixture/'private/review').glob('*.json')):
 d=json.loads(p.read_text())
 with tempfile.TemporaryDirectory() as tmp:
  t=pathlib.Path(tmp)
  for n,v in d['files'].items():(t/n).write_text(v)
  (t/'check.py').write_text(d['executable_assertions'])
  proc=subprocess.run(['python3','-B','check.py'],cwd=t,capture_output=True,text=True)
  results.append({'id':d['id'],'expected':d['expected_verdict'],'exit':proc.returncode,'stderr':proc.stderr})
ns={};d=json.loads((fixture/'private/review/9de841f5d10f.json').read_text());exec(d['files']['core.py'],ns)
try: value=ns['total'](['100000000000000000000000000.00'])
except Exception as e: value=type(e).__name__+': '+str(e)
results.append({'probe':'clean money finite 1e26','observed':value,'required':'100000000000000000000000000.00'})
# Independent integer-cents control demonstrates the expected result is representable.
assert format(10**28//100,'d')+'.00'=='100000000000000000000000000.00'
results.append({'probe':'streaming claimed example','observed':sum((s.splitlines() for s in ['a\r','\nb']),[]),'claimed':['a','','','b'],'required':['a','b']})
(out/'semantic-probes.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results[-2:],indent=2))
print('oracle observations',len(results)-2)
print('review sha256',hashlib.sha256((out/'flash-first.json').read_bytes()).hexdigest())
