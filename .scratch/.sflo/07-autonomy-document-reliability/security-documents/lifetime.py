"""Second-attempt owner death, cancellation and deadline with fake-client children."""
import json,os,pathlib,subprocess,sys,tempfile,time,types
from unittest.mock import patch
import probe
d=probe.d;os.environ['PYTHONPATH']=str(probe.FROZEN)
class Client:
 config={'model':'local'};endpoint='http://127.0.0.1:1'
 def __init__(self,root):self.root=root
 def request(self,*args,**kwargs):
  log=self.root/'calls';n=len(log.read_text().splitlines()) if log.exists() else 0
  with log.open('a') as stream:stream.write(str(os.getpid())+'\n')
  if n==0:return probe.response('{bad')
  (self.root/'second-child').write_text(str(os.getpid()))
  while True:time.sleep(.05)
def alive(pid):
 try:return pathlib.Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
 except FileNotFoundError:return False
if len(sys.argv)>1:
 root=pathlib.Path(sys.argv[1]);store,evidence,unused,answer=probe.fixture(root)
 (root/'identity.json').write_text(json.dumps({'evidence':evidence['id'],'store':str(store.root)}))
 store.answer(evidence['id'],Client(root));raise SystemExit
rows=[]
for mode in ['owner-sigkill-second','cancel-second','deadline-second']:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  root=pathlib.Path(td);started=time.monotonic();owner=None;error=None
  if mode=='owner-sigkill-second':
   owner=subprocess.Popen([sys.executable,__file__,str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   until=time.monotonic()+10
   while not (root/'second-child').exists() and time.monotonic()<until:time.sleep(.02)
   assert (root/'second-child').exists()
   identity=json.loads((root/'identity.json').read_bytes());store=d.DocumentStore(identity['store']);evidence={'id':identity['evidence']}
   second=int((root/'second-child').read_text());owner.kill();stdout,stderr=owner.communicate(timeout=5);assert owner.returncode==-9
  else:
   store,evidence,unused,answer=probe.fixture(root)
   with patch.object(d,'ANSWER_SECONDS',11.3 if mode=='deadline-second' else 260):
    try:store.answer(evidence['id'],Client(root),cancelled=lambda:mode=='cancel-second' and (root/'second-child').exists())
    except ValueError as e:error=e
   assert error;second=int((root/'second-child').read_text())
  until=time.monotonic()+5
  while alive(second) and time.monotonic()<until:time.sleep(.02)
  assert not alive(second)
  with store.locked():pass
  public=probe.ids(store);stages=[p for p in store.root.iterdir() if p.name.startswith('.stage-')]
  if mode=='deadline-second':
   assert isinstance(error,d.AnswerFailure);failed=store.resolve(error.identifier);assert failed['receipt']['kind']=='answer_failure'
   assert (store.root/error.identifier/'response-1.json').is_file()
   assert len(failed['receipt']['attempts'])==2 and failed['receipt']['attempts'][1]['validation']=='inference_error'
  else:assert public=={evidence['id']}
  if mode=='owner-sigkill-second':assert len(stages)==1 and (stages[0]/'response-1.json').is_file()
  else:assert not stages
  if mode=='owner-sigkill-second':
   with patch.object(d.subprocess,'run',return_value=types.SimpleNamespace(stdout='')):store.cleanup()
  assert store.resolve(evidence['id'])['id']==evidence['id']
  rows.append({'case':mode,'calls':len((root/'calls').read_text().splitlines()),'second_child':second,'child_running_after':alive(second),'lease_released':True,'public_record_count':len(public),'private_stage_before_cleanup':len(stages),'error':str(error) if error else None,'elapsed_s':time.monotonic()-started,'cleanup_daemon_query':'controlled empty' if owner else 'not used'})
(probe.OUT/'lifetime-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
