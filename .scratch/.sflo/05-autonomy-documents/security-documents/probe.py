"""Independent local security probes; no Docker, network, model or product edits."""
import copy, hashlib, io, json, os, pathlib, signal, subprocess, sys, tempfile, time
from unittest.mock import patch, Mock
ROOT=pathlib.Path(__file__).resolve().parents[4]
CANDIDATE='fba3e2f5fe14c640818808b32242c617b7a2ed78c3b2fbb332e7080764b6f336'
SNAP=ROOT/'.gflo/security-documents/fba3e2f5'
COMMIT='dc60ee3'
# Reconstruct trusted frozen source from Git; no checked-in duplicate source tree.
manifest=subprocess.check_output(['git','show',COMMIT+':.scratch/.sflo/05-autonomy-documents/builder-candidate.json'],cwd=ROOT)
assert hashlib.sha256(manifest).hexdigest()==CANDIDATE
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',COMMIT,'gflo'],cwd=ROOT,text=True).splitlines():
 target=SNAP/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(subprocess.check_output(['git','show',COMMIT+':'+name],cwd=ROOT))
for name,expected in json.loads(manifest)['files'].items():
 assert hashlib.sha256(subprocess.check_output(['git','show',COMMIT+':'+name],cwd=ROOT)).hexdigest()==expected
sys.path.insert(0,str(SNAP))
from gflo import documents as d
from gflo.recipes import document as protocol
from gflo.recipes import document_extract as extraction
OUT=pathlib.Path(__file__).resolve().parent
APP={'url':'https://docs.python.org/3.12/library/json.html','source_version':'controlled fixture','question':'What color?'}
BODY=b'<p>Blue is a color.</p>'
ROWS=[]
def row(case,**facts): ROWS.append(dict(case=case,**facts));save()
def save(): (OUT/'results.json').write_text(json.dumps({'candidate_sha256':CANDIDATE,'measurements':'controlled local; no network/Docker/model','results':ROWS},indent=2)+'\n')
def executor(args,name,timeout,**kw):
 mounts={a.split(',dst=')[1].split(',')[0]:a.split('src=')[1].split(',')[0] for a in args if a.startswith('type=bind')}
 if args[-1]=='fetch':
  meta=dict(protocol.policy([('Content-Type','text/html'),('Content-Length',str(len(BODY))),('Cache-Control','public,max-age=60')]),url=APP['url'],status=200,connected='1.1.1.1')
  data=protocol.frame(meta,BODY)
 else:data=d.encoded(extraction.extract(pathlib.Path(mounts['/body']).read_bytes(),'text/html'))
 kw['output'].write(data);pathlib.Path(kw['inspect_path']).write_text('{"controlled_executor":true}')
 return {'exit_code':0,'output':'','stdout_bytes':len(data),'elapsed_s':0}
def inventory(store):return {str(p.relative_to(store.root)):d.digest(p.read_bytes()) for p in store.root.rglob('*') if p.is_file() and not any(x.startswith('.') for x in p.relative_to(store.root).parts)}

def publication_probes():
 for mode in ['control','final-sync-failure','final-sync-and-retirement-failure']:
  with tempfile.TemporaryDirectory(prefix='gflo-document-security-') as temp:
   store=d.DocumentStore(pathlib.Path(temp)/'store',executor=executor);good=store.acquire(APP);before=inventory(store)
   original_sync=d.sync_directory; original_rename=pathlib.Path.rename; attempted=[]
   def sync(path):
    path=pathlib.Path(path)
    if mode!='control' and d.HEX.fullmatch(path.name) and not (path/'pending').exists():
     attempted.append(path.name);raise OSError('controlled final record fsync failure')
    return original_sync(path)
   def rename(path,target):
    if mode.endswith('retirement-failure') and d.HEX.fullmatch(path.name) and pathlib.Path(target).name.startswith('.stage-'):
     raise OSError('controlled retirement rename failure')
    return original_rename(path,target)
   error=None
   try:
    with patch.object(d,'sync_directory',side_effect=sync),patch.object(pathlib.Path,'rename',rename):result=store.acquire(APP)
   except OSError as exc:error=str(exc)
   new=[p.name for p in store.root.iterdir() if d.HEX.fullmatch(p.name) and p.name!=good['id']]
   resolvable=[]
   for identifier in new:
    try:store.resolve(identifier);resolvable.append(identifier)
    except (ValueError,OSError):pass
   assert store.resolve(good['id'])['id']==good['id']
   assert all(inventory(store).get(k)==v for k,v in before.items())
   row(mode,error=error,new_ids=new,new_resolvable_ids=resolvable,prior_good_unchanged=True,bug_observed=bool(error and resolvable))
   if mode=='control':assert len(resolvable)==1 and error is None
   elif mode=='final-sync-failure':assert not resolvable and error
   else:assert error and len(resolvable)==1

def cleanup_probes():
 for mode in ['ordinary-cleanup125','cleanup-timeout-exception','cleanup-failure-masked-by-timeout','cleanup-failure-masked-by-cancel']:
  with tempfile.TemporaryDirectory(prefix='gflo-document-cleanup-') as temp:
   def failed(*args,**kwargs):
    if mode=='cleanup-timeout-exception':raise subprocess.TimeoutExpired(['docker','rm','-f','controlled-owned'],30)
    return {'exit_code':{'ordinary-cleanup125':125,'cleanup-failure-masked-by-timeout':124,'cleanup-failure-masked-by-cancel':130}[mode], 'output':'Container cleanup failed; resume requires successful cleanup'}
   store=d.DocumentStore(pathlib.Path(temp)/'store',executor=failed)
   try:store.acquire(APP)
   except Exception as exc:error=type(exc).__name__+': '+str(exc)
   else:raise AssertionError('fault unexpectedly accepted')
   marker=(store.root/'.cleanup-required').exists();store.executor=executor;retry=None
   try:retry=store.acquire(APP)['id']
   except ValueError:pass
   row(mode,error=error,cleanup_required_marker=marker,retry_published=retry is not None,bug_observed=retry is not None)
   if mode=='ordinary-cleanup125':assert marker and retry is None
   else:assert not marker and retry is not None

if __name__=='__main__':
 publication_probes()
 cleanup_probes()
 print(json.dumps(ROWS,indent=2))
