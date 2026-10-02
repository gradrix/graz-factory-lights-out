"""Independent real-Docker acceptance/repair probe; writes only scratch fixtures."""
import json, subprocess, tempfile
from pathlib import Path
from qa_pinned import activate
activate('002cf415584b4b1e39f24dc9ff564a5b67ed5c76')
from gflo.runner import Factory
from gflo.sandbox import Sandbox
root = Path(tempfile.mkdtemp(prefix='qa-resumed-', dir=Path(__file__).resolve().parent))
repo=root/'repo';repo.mkdir();(repo/'app.py').write_text('value=2\n')
for command in [['git','init','-q',str(repo)],['git','-C',str(repo),'add','.'],['git','-C',str(repo),'-c','user.name=QA','-c','user.email=qa@local','commit','-qm','fixture']]: subprocess.run(command,check=True)
a=root/'acceptance';a.mkdir();(a/'check.py').write_text("from pathlib import Path\nassert Path('/workspace/app.py').read_text() == 'value=2\\n'\n")
task=root/'task.json';task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(a),objective='Set value to 2 and add Python unittest regressions',checks=[['python','-I','/acceptance/check.py']],max_attempts=2)))
results=[]
for kind in ['clean','generated-repair','external-failure','generated-import-error']:
 calls=[];previous=[]
 def worker(w,t,p,n):
  previous.append(p)
  (w/'tests').mkdir(exist_ok=True)
  assertion='self.assertEqual(2, 2)'
  if kind=='generated-repair' and n==1: assertion='self.assertEqual(2, 3)'
  (w/'tests/test_value.py').write_text('import unittest\nclass Value(unittest.TestCase):\n def test_value(self): '+assertion+'\n')
  if kind=='external-failure':(w/'app.py').write_text('value=3\n')
  if kind=='generated-import-error':(w/'tests/test_value.py').write_text('raise RuntimeError("import failed")\n')
  return {}
 def reviewer(*args):
  calls.append(True)
  return dict(decision='pass',findings=[],question='')
 s=Sandbox();f=Factory(root/kind,worker,s.verify,reviewer=reviewer);rid=f.create(task);r=f.resume(rid)
 expected='exhausted' if kind in ['external-failure','generated-import-error'] else 'accepted'
 assert r['status']==expected,(kind,r)
 assert len(calls)==(1 if expected=='accepted' else 0),(kind,calls)
 if kind=='generated-repair':
  assert r['attempts']==2 and previous[1]['passed'] is False
  assert [x['exit_code'] for x in previous[1]['checks']]==[0,1]
 if kind=='external-failure': assert [x['exit_code'] for x in previous[1]['checks']]==[1,0]
 if expected=='accepted':
  assert f.resume(rid)['status']=='accepted'
  receipt=Path(r['directory'])/'attempts'/str(r['attempts'])/'verification.json'
  receipt.write_text('{}')
  assert f.status(rid)['status']=='invalidated'
 results.append(dict(case=kind,status=r['status'],attempts=r['attempts'],review_calls=len(calls),run=r['directory']))
# Verifier-chosen negative control: generated green cannot substitute for frozen checks.
bad=root/'empty-checks.json';data=json.loads(task.read_text());data['checks']=[];bad.write_text(json.dumps(data))
try:f.create(bad)
except ValueError as error:assert 'nonempty' in str(error)
else:raise AssertionError('empty external checks accepted')
(root/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(dict(evidence=str(root),results=results),indent=2))
