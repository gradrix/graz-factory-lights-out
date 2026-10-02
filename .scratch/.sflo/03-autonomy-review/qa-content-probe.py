import json,subprocess
from qa_pinned import activate,evidence
activate('04c7ef6111e6ed0aef07842528b3137f6a39e7f8')
from gflo.runner import Factory
from gflo.sandbox import Sandbox
ROOT=evidence('qa-content-evidence');ROOT.mkdir(exist_ok=True)
repo=ROOT/'repo';repo.mkdir();(repo/'app.py').write_text('value=2\n')
for cmd in [['git','init','-q',str(repo)],['git','-C',str(repo),'add','.'],['git','-C',str(repo),'-c','user.name=QA','-c','user.email=qa@local','commit','-qm','fixture']]:subprocess.run(cmd,check=True)
a=ROOT/'acceptance';a.mkdir();(a/'check.py').write_text('assert True\n')
task=ROOT/'task.json';task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(a),objective='Set value to 2; remove temporary build artifacts',checks=[['python','-I','/acceptance/check.py']],max_attempts=2)))
results=[]
for kind in ['clean','binary','symlink','oversize','empty','persistent-binary','invalid-review']:
 feedback=[]; reviews=[]
 def worker(w,t,p,n):
  feedback.append(p)
  if n==1 or kind=='persistent-binary':
   if kind in ('binary','persistent-binary'):(w/'cache.pyc').write_bytes(b'\xff\x00')
   if kind=='symlink':(w/'link.py').symlink_to('app.py')
   if kind=='oversize':(w/'large.txt').write_text('x'*200001)
   if kind=='empty':(w/'app.py').unlink()
  else:
   assert p['reviewability']['passed'] is False
   for name in ['cache.pyc','link.py','large.txt']:(w/name).unlink(missing_ok=True)
   (w/'app.py').write_text('value=2\n')
  return {}
 def reviewer(*a):
  reviews.append(True)
  return {'decision':'pass'} if kind=='invalid-review' else {'decision':'pass','findings':[],'question':''}
 sandbox=Sandbox();f=Factory(ROOT/kind,worker,sandbox.verify,reviewer=reviewer);rid=f.create(task)
 try:r=f.resume(rid)
 except ValueError:r=f.status(rid)
 expected='exhausted' if kind=='persistent-binary' else 'interrupted' if kind=='invalid-review' else 'accepted'
 assert r['status']==expected,(kind,r)
 assert len(reviews)==(0 if kind=='persistent-binary' else 1),(kind,reviews)
 if kind not in ('clean','invalid-review'):assert r['attempts']==2
 results.append(dict(kind=kind,expected=expected,actual=r['status'],attempts=r['attempts'],review_calls=len(reviews),run=rid))
(ROOT/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
