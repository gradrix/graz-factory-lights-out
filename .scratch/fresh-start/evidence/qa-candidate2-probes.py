import sys,os,json,hashlib,time,signal,multiprocessing,subprocess
from pathlib import Path
ROOT=Path('/tmp/gflo-review-candidate2')
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_runner import RunnerTests
from gflo.runner import Factory
from gflo.sandbox import Sandbox
manifest=json.loads(Path(__file__).with_name('candidate2.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in manifest['files'].items())
print('MANIFEST_OK',manifest['identity'])
def fixture():
 t=RunnerTests();t.setUp();return t
for crash in [False,True]:
 t=fixture();f=Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True});rid=f.create(t.task)
 if crash:
  pid=os.fork()
  if pid==0:
   original=Path.mkdir
   def mkdir(path,*args,**kwargs):
    result=original(path,*args,**kwargs)
    if path.name=='1' and path.parent.name=='attempts':os._exit(77)
    return result
   Path.mkdir=mkdir;f.resume(rid);os._exit(0)
  _,status=os.waitpid(pid,0);assert os.waitstatus_to_exitcode(status)==77
 assert Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True}).resume(rid)['status']=='accepted'
 print('QA-01 PASS crash=',crash);t.doCleanups()
for artifact in [None,'workspace/app.py','change.patch','task.json']:
 t=fixture();f=Factory(t.root/'state',lambda *a:{},lambda *a:{'passed':True});rid=f.create(t.task);f.resume(rid)
 if artifact:
  (f.state/rid/artifact).write_text('changed')
  assert f.status(rid)['status']=='invalidated'
  try:f.resume(rid)
  except ValueError:pass
  else:raise AssertionError('Accepted tampered artifact')
 else:assert f.resume(rid)['status']=='accepted'
 print('QA-02 PASS artifact=',artifact);t.doCleanups()
t=fixture();s=Sandbox()
def worker(w,*args):
 (w/'app.py').write_text('value = 2\n');return {}
f=Factory(t.root/'state',worker,lambda w,*a:{'passed':(w/'app.py').read_text()=='value = 2\n'},cleanup=s.cleanup)
rid=f.create(t.task);w=f.state/rid/'workspace'
def launch():s.execute(w,['sh','-c','while true; do date +%s%N > tick; sleep 0.1; done'])
p=multiprocessing.Process(target=launch);p.start()
for _ in range(100):
 if (w/'tick').exists():break
 time.sleep(.05)
assert (w/'tick').exists();os.kill(p.pid,signal.SIGKILL);p.join()
a=(w/'tick').read_text();time.sleep(.3);assert a!=(w/'tick').read_text()
r=f.resume(rid);assert r['status']=='accepted';a=(w/'tick').read_text();time.sleep(.3);assert a==(w/'tick').read_text()
print('QA-03 PASS orphan stopped by resume')
assert (t.repo/'app.py').read_text()=='value = 0\n'
subprocess.run(['git','-C',str(t.repo),'apply','--check',r['patch']],check=True)
subprocess.run(['git','-C',str(t.repo),'apply',r['patch']],check=True)
assert (t.repo/'app.py').read_text()=='value = 2\n'
print('PATCH_APPLIES PASS')
cli=subprocess.run([sys.executable,'-m','gflo','--state',str(f.state),'status',rid],cwd=ROOT,capture_output=True,text=True,check=True)
assert json.loads(cli.stdout)['status']=='accepted'
print('CLI_STATUS PASS');t.doCleanups()
