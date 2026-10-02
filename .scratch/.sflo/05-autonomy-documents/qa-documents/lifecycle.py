import pathlib,sys,tempfile,json,shutil,time,subprocess,hashlib
sys.path.insert(0,str(pathlib.Path.cwd()))
import gflo.documents as d
from gflo.recipes.document import frame
from gflo import guard
OUT=pathlib.Path(__file__).resolve().parent;APP={'url':'https://docs.python.org/3.12/library/json.html','source_version':'QA delayed private helper','question':'fixture'}
if len(sys.argv)>1:
 d.HELPERS=pathlib.Path(sys.argv[2]);d.DocumentStore(sys.argv[1]).acquire(APP);raise AssertionError('unexpected completion')
ROOT=pathlib.Path(tempfile.mkdtemp(prefix='gflo-doc-life-'));helpers=ROOT/'helpers';shutil.copytree(d.HELPERS,helpers);rows=[]
def save():(OUT/'lifecycle-results.json').write_text(json.dumps({'root':str(ROOT),'rows':rows},indent=2)+'\n')
def absent(name):return subprocess.run(['docker','inspect',name],capture_output=True,timeout=10).returncode!=0
# Kill owner during real fetch container, whose private helper waits instead of contacting DNS/network.
(helpers/'document.py').write_text('import time;time.sleep(60)\n');store=d.DocumentStore(ROOT/'death');owner=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),str(store.root),str(helpers)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);owned=[]
try:
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  paths=list(store.root.glob('.work-*/fetch-inspect.json'))
  if paths:
   facts=json.loads(paths[0].read_text());name=facts['name'];state=subprocess.run(['docker','inspect','--format','{{.State.Running}}',name],capture_output=True,text=True,timeout=5)
   if state.stdout.strip()=='true':owned=[name];break
  time.sleep(.1)
 assert owned;owner.kill();owner.wait(timeout=5);started=time.monotonic()
 while time.monotonic()-started<10 and not absent(name):time.sleep(.1)
 assert absent(name);assert not [p for p in store.root.iterdir() if d.HEX.fullmatch(p.name)]
 store.cleanup();assert not list(store.root.glob('.work-*')) and not list(store.root.glob('.stage-*'));rows.append({'phase':'fetch-owner-SIGKILL','actual':facts,'container_removed':True,'no_receipt':True,'explicit_recovery':True});save()
finally:
 if owner.poll() is None:owner.kill();owner.wait()
 for n in owned:subprocess.run(['docker','rm','-f',n],capture_output=True,timeout=10)
# Cancel actual offline extraction; fetch is an identified in-memory fixture stream.
shutil.copyfile(d.HELPERS/'document.py',helpers/'document.py');(helpers/'document_extract.py').write_text('import time;time.sleep(60)\n');d.HELPERS=helpers;started=None;facts=[]
def executor(args,name,timeout,**kw):
 global started
 if args[-1]=='fetch':
  body=b'<p>fixture</p>';metadata={'url':APP['url'],'status':200,'content_type':'text/html','charset':'utf-8','cache_control':'public','connected':'1.1.1.1','body_size':len(body),'http_headers':{'content-type':'text/html','cache-control':'public','content-length':str(len(body))}};kw['output'].write(frame(metadata,body));pathlib.Path(kw['inspect_path']).write_text('{"QA":"in-memory fetch"}');return {'exit_code':0,'output':''}
 started=time.monotonic()
 try:return guard.run(args,name,timeout,**kw)
 finally:facts.append(json.loads(pathlib.Path(kw['inspect_path']).read_text()))
store=d.DocumentStore(ROOT/'cancel',executor=executor)
try:store.acquire(APP,cancelled=lambda:started is not None and time.monotonic()-started>1)
except ValueError as e:assert 'cancel' in str(e).lower()
else:raise AssertionError('cancel accepted')
assert facts and all(absent(f['name']) for f in facts);assert not [p for p in store.root.iterdir() if p.name!='.lock'];rows.append({'phase':'offline-extraction-cancel','actual':facts,'container_removed':True,'no_receipt':True});save();print('PASS actual fetch owner death and extraction cancellation')
