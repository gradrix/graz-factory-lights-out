import sys,tempfile,subprocess,json,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from gflo.runner import Factory
from gflo.observe import Observer
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);repo=root/'repo';repo.mkdir();(repo/'a').write_text('a')
 for args in (['init','-q'],['add','.'],['-c','user.name=QA','-c','user.email=qa@local','commit','-qm','base']):subprocess.run(['git','-C',str(repo),*args],check=True)
 accept=root/'a';accept.mkdir();(accept/'check').write_text('true')
 task=root/'task';task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(accept),objective='Keep a',checks=[['true']])))
 f=Factory(root/'state',None,None);obs=Observer(f.state)
 run=f.create(task);f.cancel(run);assert obs.status(run)['status']=='cancelled';print('Control: inactive pending cancellation -> cancelled PASS',flush=True)
 run=f.create(task)
 code="""import sys,time
from pathlib import Path
from gflo.runner import Factory
def cleanup(w):
 Path(sys.argv[3]).touch();time.sleep(30)
f=Factory(sys.argv[1],lambda *a:{},lambda *a:{'passed':True},cleanup)
f.resume(sys.argv[2])
"""
 marker=root/'started';p=subprocess.Popen([sys.executable,'-c',code,str(f.state),run,str(marker)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(200):
   if marker.exists():break
   time.sleep(.01)
  assert marker.exists();f.cancel(run);p.wait(timeout=10);s=obs.status(run)
  print('Startup cancellation status:',json.dumps({k:s[k] for k in ('status','phase','owner_alive','cancel_requested')}),flush=True)
  assert s['status']=='cancelled',s
 finally:
  if p.poll() is None:p.kill();p.wait()
