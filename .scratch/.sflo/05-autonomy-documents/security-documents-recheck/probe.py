"""Controlled independent D1/D2 repair recheck; no Docker/network/model calls."""
import hashlib, json, os, pathlib, signal, subprocess, sys, tempfile, time
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[4];OUT=pathlib.Path(__file__).resolve().parent
CANDIDATE='9c01da103e9f145bfc426e4a4c3f02780b85a845594a4716d1437d36c413cb3c'
SNAP=ROOT/'.gflo/security-documents/9c01da10'
COMMIT='2049361'
manifest=subprocess.check_output(['git','show',COMMIT+':.scratch/.sflo/05-autonomy-documents/builder-candidate-v2.json'],cwd=ROOT)
assert hashlib.sha256(manifest).hexdigest()==CANDIDATE
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',COMMIT,'gflo'],cwd=ROOT,text=True).splitlines():
 target=SNAP/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(subprocess.check_output(['git','show',COMMIT+':'+name],cwd=ROOT))
for name,expected in json.loads(manifest)['files'].items():
 assert hashlib.sha256(subprocess.check_output(['git','show',COMMIT+':'+name],cwd=ROOT)).hexdigest()==expected
sys.path.insert(0,str(SNAP))
from gflo import documents as d
from gflo.recipes import document as p,document_extract as x
APP={'url':'https://docs.python.org/3.12/library/json.html','source_version':'controlled fixture','question':'What color?'}
BODY=b'<p>Blue is a color.</p>';ROWS=[]
def row(case,**facts):ROWS.append(dict(case=case,**facts));(OUT/'results.json').write_text(json.dumps({'candidate_sha256':CANDIDATE,'results':ROWS},indent=2)+'\n')
def executor(args,name,timeout,**kw):
 mounts={a.split(',dst=')[1].split(',')[0]:a.split('src=')[1].split(',')[0] for a in args if a.startswith('type=bind')}
 if args[-1]=='fetch':
  meta=dict(p.policy([('Content-Type','text/html'),('Content-Length',str(len(BODY)))]),url=APP['url'],status=200,connected='1.1.1.1');data=p.frame(meta,BODY)
 else:data=d.encoded(x.extract(pathlib.Path(mounts['/body']).read_bytes(),'text/html'))
 kw['output'].write(data);pathlib.Path(kw['inspect_path']).write_text('{"controlled_executor":true}')
 return {'exit_code':0,'output':'','stdout_bytes':len(data),'elapsed_s':0}
def ids(store):return {p.name for p in store.root.iterdir() if d.HEX.fullmatch(p.name)}
def inventory(store):return {str(p.relative_to(store.root)):d.digest(p.read_bytes()) for p in store.root.rglob('*') if p.is_file() and not any(s.startswith('.') for s in p.relative_to(store.root).parts)}
def reject(fn):
 try:fn()
 except (ValueError,OSError,subprocess.SubprocessError,RuntimeError):return
 raise AssertionError('fault not rejected')
def recover(store):
 with patch.object(d.subprocess,'run') as run:
  run.return_value.stdout='';store.cleanup()
 assert not (store.root/'.cleanup-required').exists()

def publication():
 for mode in ['control','original-postcommit-faults','first-stage-sync','last-stage-sync','last-sync-plus-cleanup','final-rename','pending-unlink','final-validation','cancel-last-stage-sync','postcommit-I/O-prohibited']:
  with tempfile.TemporaryDirectory() as td:
   store=d.DocumentStore(pathlib.Path(td)/'store',executor=executor);good=store.acquire(APP);before=inventory(store);prior=ids(store);cancel=[False];committed=[False];syncs=[0]
   osync=d.sync_directory;orename=pathlib.Path.rename;ounlink=pathlib.Path.unlink;oexists=pathlib.Path.exists;oresolve=store._resolve;ormtree=d.shutil.rmtree
   def sync(path):
    path=pathlib.Path(path)
    if d.HEX.fullmatch(path.name):raise AssertionError('postcommit sync')
    if path.name.startswith('.stage-'):
     syncs[0]+=1
     if mode=='first-stage-sync' and syncs[0]==1:raise OSError('stage sync1')
     if mode in ['last-stage-sync','last-sync-plus-cleanup'] and syncs[0]==2:raise OSError('stage sync2')
     if mode=='cancel-last-stage-sync' and syncs[0]==2:cancel[0]=True
    return osync(path)
   def rename(path,target):
    if d.HEX.fullmatch(path.name):raise AssertionError('retirement unexpectedly attempted')
    if mode=='final-rename':raise OSError('commit rename unavailable')
    result=orename(path,target);committed[0]=True;return result
   def unlink(path,*a,**kw):
    if path.name=='pending' and mode=='pending-unlink':raise OSError('pending unlink unavailable')
    return ounlink(path,*a,**kw)
   def resolve(*a,**kw):
    if mode=='final-validation' and kw.get('staging') is not None:raise ValueError('staged invalid')
    if mode=='postcommit-I/O-prohibited' and committed[0]:raise AssertionError('postcommit read')
    return oresolve(*a,**kw)
   def exists(path):
    if committed[0] and path.name.startswith('.stage-'):raise AssertionError('postcommit stat')
    return oexists(path)
   def rmtree(path,*a,**kw):
    if mode=='last-sync-plus-cleanup' and pathlib.Path(path).name.startswith('.stage-'):raise OSError('staging cleanup unavailable')
    if committed[0]:raise AssertionError('postcommit cleanup')
    return ormtree(path,*a,**kw)
   error=None
   try:
    with patch.object(d,'sync_directory',sync),patch.object(pathlib.Path,'rename',rename),patch.object(pathlib.Path,'unlink',unlink),patch.object(pathlib.Path,'exists',exists),patch.object(store,'_resolve',resolve),patch.object(d.shutil,'rmtree',rmtree):
     record=store.acquire(APP,cancelled=lambda:cancel[0])
   except (OSError,ValueError) as exc:error=str(exc)
   assert all(inventory(store).get(k)==v for k,v in before.items());assert store.resolve(good['id'])['id']==good['id']
   success=mode in ['control','original-postcommit-faults','postcommit-I/O-prohibited']
   assert (error is None)==success
   assert len(ids(store)-prior)==(1 if success else 0)
   if mode=='last-sync-plus-cleanup':reject(lambda:store.acquire(APP));recover(store);store.acquire(APP)
   row('publication-'+mode,passed=True,operation_succeeded=success,error=error,prior_good_unchanged=True,postcommit_filesystem_operations=0)


def answers():
 with tempfile.TemporaryDirectory() as td:
  store=d.DocumentStore(pathlib.Path(td)/'store',executor=executor);e=store.acquire(APP)
  client=type('C',(),{'config':{'model':'local'},'endpoint':'http://127.0.0.1:1'})()
  value={'status':'supported','claims':[{'text':'Blue','citations':[{'evidence_id':e['id'],'span':1,'excerpt':'Blue'}]}],'reason':''}
  response={'choices':[{'message':{'content':json.dumps(value)}}]};orename=pathlib.Path.rename;oresolve=store._resolve;committed=[False]
  def rename(path,target):result=orename(path,target);committed[0]=True;return result
  def resolve(*a,**kw):
   if committed[0]:raise AssertionError('answer postcommit read')
   return oresolve(*a,**kw)
  with patch.object(d,'bounded_answer',return_value=response),patch.object(pathlib.Path,'rename',rename),patch.object(store,'_resolve',resolve):saved=store.answer(e['id'],client)
  assert store.replay(saved['id'])['answer']==value
  row('answer-render-before-commit-and-offline-replay',passed=True)


def cleanup():
 outcomes=[1,124,125,130,RuntimeError('cleanup failure'),OSError('docker inaccessible'),subprocess.TimeoutExpired(['docker','rm','-f','owned'],30)]
 for phase in ['fetch','extract']:
  for outcome in outcomes:
   with tempfile.TemporaryDirectory() as td:
    store=d.DocumentStore(pathlib.Path(td)/'store',executor=executor);good=store.acquire(APP);before=inventory(store);called=[0]
    def uncertain(args,*a,**kw):
     called[0]+=1
     if args[-1]!=phase:return executor(args,*a,**kw)
     assert (store.root/'.cleanup-required').exists()
     if isinstance(outcome,Exception):raise outcome
     return {'exit_code':outcome,'output':'controlled failure'}
    store.executor=uncertain;reject(lambda:store.acquire(APP));assert (store.root/'.cleanup-required').exists();count=called[0];reject(lambda:store.acquire(APP));assert called[0]==count
    assert inventory(store)==before;assert store.resolve(good['id'])['id']==good['id']
    with patch.object(d.subprocess,'run',side_effect=subprocess.TimeoutExpired('cleanup',15)):reject(store.cleanup)
    assert (store.root/'.cleanup-required').exists();recover(store);store.executor=executor;store.acquire(APP)
    row('cleanup-'+phase+'-'+str(outcome),passed=True,retry_refused_before_executor=True,failed_recovery_kept_fence=True,explicit_recovery_then_success=True,prior_good_unchanged=True)


def ownerdeath():
 for point in ['before-rename','after-rename']:
  with tempfile.TemporaryDirectory() as td:
   store=d.DocumentStore(pathlib.Path(td)/'store',executor=executor);good=store.acquire(APP);prior=ids(store);pid=os.fork()
   if pid==0:
    original=pathlib.Path.rename
    def rename(path,target):
     if point=='after-rename':original(path,target)
     os.kill(os.getpid(),signal.SIGKILL)
    with patch.object(pathlib.Path,'rename',rename):store.acquire(APP)
    os._exit(3)
   _,status=os.waitpid(pid,0);assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL
   new=ids(store)-prior
   assert len(new)==(1 if point=='after-rename' else 0)
   for identifier in new:assert store.resolve(identifier)['id']==identifier
   assert store.resolve(good['id'])['id']==good['id']
   if point=='before-rename':reject(lambda:store.acquire(APP));recover(store)
   row('actual-owner-SIGKILL-'+point,passed=True,new_ids_resolvable=len(new),prior_good_preserved=True)

if __name__=='__main__':publication();answers();cleanup();ownerdeath();print('PASS',len(ROWS),'independent repair probes')
