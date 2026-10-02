import contextlib,io,json,pathlib,sys,tempfile,subprocess
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('f5b5491')
from gflo.__main__ import main
from gflo.environment import EnvironmentStore
from gflo.runner import Factory
from gflo.sandbox import Sandbox
out=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(tempfile.mkdtemp(prefix='gflo-stdlib-qa-'));store=root/'store';args=['--config','/nonexistent/config','environment','--store',str(store)]
with contextlib.redirect_stdout(io.StringIO()) as s:assert main(args+['prepare','python-stdlib'])==0
prepared=json.loads(s.getvalue());env=EnvironmentStore(store).resolve(prepared['id'])
with contextlib.redirect_stdout(io.StringIO()) as s:assert main(args+['prepare','python-stdlib'])==0
assert json.loads(s.getvalue())['id']==env.id
with contextlib.redirect_stdout(io.StringIO()) as s:assert main(args+['inspect',env.id])==0
receipt=json.loads(s.getvalue());(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
with contextlib.redirect_stdout(io.StringIO()) as s:assert main(args+['check',env.id,'--repeat','2'])==0
checks=json.loads(s.getvalue());assert all(c['passed'] for c in checks['checks']);(out/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
repo=root/'repo';repo.mkdir();(repo/'app.py').write_text('value=42\n')
for cmd in [['git','init','-q',str(repo)],['git','-C',str(repo),'add','.'],['git','-C',str(repo),'-c','user.name=QA','-c','user.email=qa@local','commit','-qm','fixture']]:subprocess.run(cmd,check=True)
a=root/'acceptance';a.mkdir();(a/'check.py').write_text('from pathlib import Path\nassert Path("/workspace/app.py").read_text()=="value=42\\n"\n')
task=root/'task.json';task.write_text(json.dumps({'repo':str(repo),'acceptance':str(a),'objective':'Preserve42','checks':[['python','-I','/acceptance/check.py']],'max_attempts':2}))
sandbox=Sandbox('sha256:'+'0'*64);calls=[]
def worker(w,t,p,n):
 calls.append(t)
 r=sandbox.execute(w,['python','-c','import json,os,platform;print(json.dumps({"python":platform.python_version(),"deps_mode":oct(os.stat("/opt/deps").st_mode&511)}))']);assert r['exit_code']==0 and r['image']==env.image
 try:r=sandbox.execute(w,['python','-c','open("/opt/deps/no-write","w").write("x")'])
 except Exception:raise
 assert r['exit_code']!=0
 return {}
f=Factory(root/'state',worker,sandbox.verify,environment=env,bind_environment=sandbox.bind);rid=f.create(task)
# Restart with deliberately wrong config image but original frozen binding.
f.db.close();f=Factory(root/'state',worker,sandbox.verify,bind_environment=sandbox.bind);assert f.resume(rid)['status']=='accepted';assert len(calls)==1
assert f.resume(rid)['status']=='accepted'
env.dependencies.chmod(0o755)
status=f.status(rid)['status']
assert status=='invalidated'
try:f.resume(rid)
except ValueError:resume='rejected'
else:raise AssertionError('tampered accepted run resumed')
from gflo.observe import Observer
assert Observer(root/'state').status(rid)['status']=='invalidated'
result={'candidate':'f5b5491','root':str(root),'environment':env.id,'run':rid,'stable_prepare':True,'check_twice':True,'restart_frozen_image':True,'dependency_write_rejected':True,'tampered_accepted_status':status,'tampered_accepted_resume':resume}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
