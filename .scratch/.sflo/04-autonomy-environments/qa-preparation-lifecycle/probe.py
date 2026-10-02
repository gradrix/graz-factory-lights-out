import json,pathlib,sys,tempfile,subprocess,time,os,signal,threading
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('25f75c3275739cc7cc2a4fc5a4e16580b81511d1')
import gflo.prepare as prep
from gflo.environment import EnvironmentStore
OUT=pathlib.Path(__file__).resolve().parent
if len(sys.argv)>1:
 store=EnvironmentStore(sys.argv[1]);prep.EMPTY_ARCHIVE='import time;time.sleep(60)';prep.prepare(store,'python-stdlib',timeout=90);raise AssertionError('unexpected completed preparation')
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='gflo-lifecycle-qa-'));rows=[]
def save():(OUT/'results.json').write_text(json.dumps({'candidate':'25f75c3275739cc7cc2a4fc5a4e16580b81511d1','root':str(ROOT),'results':rows},indent=2)+'\n')
def names(store):
 return [json.loads(p.read_text())['name'] for p in store.root.glob('.work-*/*.json')]
def absent(name):return subprocess.run(['docker','inspect',name],capture_output=True,timeout=10).returncode!=0
def no_receipt(store):assert not [p for p in store.root.iterdir() if not p.name.startswith('.')]
# Capture owned names before preparation's normal cleanup removes the receipts.
realexecute=prep.execute;owned=[]
def capture(*a,**kw):
 try:return realexecute(*a,**kw)
 finally:
  for p in pathlib.Path(a[2]).glob('*.json'):
   try:owned.append(json.loads(p.read_text())['name'])
   except (ValueError,KeyError):pass
prep.execute=capture;original=prep.EMPTY_ARCHIVE;prep.EMPTY_ARCHIVE='import time;time.sleep(60)'
for mode in ['timeout','cancel']:
 owned.clear();store=EnvironmentStore(ROOT/mode);started=time.monotonic();cancel=threading.Event();timer=threading.Timer(2,cancel.set) if mode=='cancel' else None
 if timer:timer.start()
 try:
  prep.prepare(store,'python-stdlib',timeout=3 if mode=='timeout' else 20,cancelled=cancel.is_set)
 except ValueError as e:error=str(e)
 else:raise AssertionError(mode+' succeeded')
 finally:
  if timer:timer.cancel()
 no_receipt(store);assert owned and all(absent(n) for n in owned);rows.append({'case':mode,'error':error,'elapsed':time.monotonic()-started,'owned':owned.copy(),'removed':True,'no_receipt':True});save()
prep.EMPTY_ARCHIVE=original;prep.execute=realexecute
store=EnvironmentStore(ROOT/'sigkill');log=(OUT/'owner.log').open('w');owner=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),str(store.root)],stdout=log,stderr=subprocess.STDOUT)
try:
 deadline=time.monotonic()+20;owned=[]
 while time.monotonic()<deadline:
  owned=names(store)
  if owned:
   state=subprocess.run(['docker','inspect','--format','{{.State.Running}}',owned[0]],capture_output=True,text=True,timeout=10)
   if state.stdout.strip()=='true':break
  time.sleep(.1)
 else:raise AssertionError('owner container never running')
 owner.kill();owner.wait(timeout=10);started=time.monotonic()
 while time.monotonic()-started<15 and not all(absent(n) for n in owned):time.sleep(.1)
 assert all(absent(n) for n in owned);no_receipt(store);rows.append({'case':'actual-owner-SIGKILL','owner_exit':owner.returncode,'owned':owned,'removed':True,'cleanup_elapsed':time.monotonic()-started,'no_receipt':True});save()
finally:
 if owner.poll() is None:owner.kill();owner.wait()
 log.close()
 for n in owned:subprocess.run(['docker','rm','-f',n],capture_output=True,timeout=15)
# Actual configured limits, bounded finite programs in offline preparation containers.
programs={
'scratch-full':"import errno,json\ntry:\n with open('/tmp/fill','wb') as f:\n  for _ in range(20):f.write(b'x'*1048576)\nexcept OSError as e:\n assert e.errno==errno.ENOSPC;print(json.dumps({'errno':e.errno,'scratch_full':True}))\nelse:raise AssertionError('scratch not capped')",
'pid-limit':"import subprocess,json\np=[]\ntry:\n for i in range(150):p.append(subprocess.Popen(['sleep','10']))\nexcept OSError as e:\n assert e.errno==11;print(json.dumps({'children':len(p),'errno':e.errno}))\nelse:raise AssertionError('PID limit absent')\nfinally:\n for c in p:c.terminate()\n for c in p:c.wait()",
'memory-limit':"chunks=[]\nfor _ in range(1200):chunks.append(bytearray(1048576))\nraise AssertionError('memory cap absent')"}
for label,code in programs.items():
 work=ROOT/label;work.mkdir();started=time.monotonic();row={'case':label}
 try:
  result,facts=prep.execute(prep.DEFAULT_IMAGE,['python','-c',code],work,timeout=30);row.update(result=result,facts=facts)
  assert label!='memory-limit'
 except ValueError as e:
  row['error']=str(e);assert label=='memory-limit' and '(137)' in str(e)
 observed=[json.loads(p.read_text()) for p in work.glob('*.json')];assert len(observed)==1;actual=observed[0];assert absent(actual['name']);row['actual']=actual;row['elapsed']=time.monotonic()-started;row['removed']=True;rows.append(row);save()
print('PASS timeout/cancel/SIGKILL/scratch/memory/PIDs')
