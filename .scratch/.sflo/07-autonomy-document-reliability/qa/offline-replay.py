"""Run only after completed answers. Actual network-none replay of private copied stores."""
import hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid
REPO=pathlib.Path('/home/gradrix/gflo-documents-2fe870d');Q=REPO/'.gflo/qualification-1';LEGACY=pathlib.Path('/home/gradrix/gflo-stage4-9c01da1/.gflo/trial-1');OUT=Q/'independent-offline-replay';IMAGE='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def record_hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file() and f!=p/'.lock'}
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
manifest=REPO/'.scratch/.sflo/07-autonomy-document-reliability/builder-candidate.json'
def frozen():
 assert sha(manifest)=='4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e'
 for n,h in json.loads(manifest.read_text())['files'].items():assert sha(REPO/n)==h,n
frozen();summary=json.loads((Q/'answers/summary.json').read_text());assert summary['status']=='complete_pending_independent_semantic_review' and len(summary['rows'])==10;assert not OUT.exists();OUT.mkdir(mode=0o700)
orig={'new':record_hashes(Q/'store'),'legacy':record_hashes(LEGACY/'store')};shutil.copytree(Q/'store',OUT/'new-store');shutil.copytree(LEGACY/'store',OUT/'legacy-store');before={n:record_hashes(OUT/(n+'-store'))for n in ['new','legacy']};assert orig==before
cases=[]
for row in summary['rows']:
 assert 'id'in row,'Unpublished answer needs independent review before replay qualification';case={'group':'new','name':row['name'],'id':row['id'],'failure':row['status']=='answer_failure'}
 if not case['failure']:case['expected']=json.loads((Q/'answers'/row['name']/'answer.json').read_text())
 cases.append(case)
for name in ['separators','unsupported_future_date']:
 answer=json.loads((LEGACY/(name+'-answer.json')).read_text());cases.append({'group':'legacy','name':name,'id':answer['id'],'failure':False,'expected':answer})
save(OUT/'cases.json',cases)
code="""import json,pathlib,sys
sys.path.insert(0,'/source')
from gflo.documents import DocumentStore
rows=[]
for case in json.loads(pathlib.Path('/cases.json').read_text()):
 store=DocumentStore('/'+case['group']+'-store');resolved=store.resolve(case['id'])
 if case['failure']:
  try:store.replay(case['id'])
  except ValueError:rows.append({'group':case['group'],'name':case['name'],'id':case['id'],'diagnostic_replay_refused':True})
  else:raise AssertionError('Failure replay accepted')
 else:
  result=store.replay(case['id']);expected=case['expected'];result.pop('age_seconds',None);expected.pop('age_seconds',None);assert result==expected,case['name'];rows.append({'group':case['group'],'name':case['name'],'id':case['id'],'format':resolved['receipt']['format'],'answer_status':result['answer']['status'],'matches_saved':True})
print(json.dumps(rows))
"""
(OUT/'child.py').write_text(code);name='gflo-doc-qa-replay-'+uuid.uuid4().hex[:12];args=['docker','create','--pull','never','--name',name,'--runtime','runc','--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','256m','--memory-swap','256m','--cpus','1','--pids-limit','64','--tmpfs','/tmp:rw,nosuid,nodev,size=16m','--env','PYTHONDONTWRITEBYTECODE=1']
for source,target,ro in [(REPO/'gflo','/source/gflo',True),(OUT/'new-store','/new-store',False),(OUT/'legacy-store','/legacy-store',False),(OUT/'child.py','/probe.py',True),(OUT/'cases.json','/cases.json',True)]:args+=['--mount',f'type=bind,src={source},dst={target}'+(',readonly' if ro else '')]
args += [IMAGE,'python','/probe.py'];started=time.monotonic();result=None
try:
 subprocess.run(args,capture_output=True,text=True,check=True,timeout=15);facts=json.loads(subprocess.check_output(['docker','inspect',name],timeout=10))[0];save(OUT/'container.json',{'id':facts['Id'],'image':facts['Image'],'host':facts['HostConfig'],'mounts':facts['Mounts'],'config':{k:facts['Config'][k]for k in ['User','Cmd','Env']}});assert facts['HostConfig']['NetworkMode']=='none';result=subprocess.run(['docker','start','-a',name],capture_output=True,text=True,timeout=30);(OUT/'stdout.json').write_text(result.stdout);(OUT/'stderr.log').write_text(result.stderr);assert result.returncode==0,result.stderr
finally:
 removal=subprocess.run(['docker','rm','-f',name],capture_output=True,text=True,timeout=30);remaining=subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+name+'$'],text=True,timeout=10).split();save(OUT/'cleanup.json',{'returncode':removal.returncode,'remaining':remaining});assert not remaining
assert before=={n:record_hashes(OUT/(n+'-store'))for n in ['new','legacy']};assert orig=={'new':record_hashes(Q/'store'),'legacy':record_hashes(LEGACY/'store')};frozen();save(OUT/'result.json',{'passed':True,'elapsed_s':time.monotonic()-started,'cases':json.loads(result.stdout),'copied_record_hashes_before':before,'original_and_copy_records_unchanged':True,'candidate_hashes_unchanged':True});print('PASS actual network-none legacy/format2 replay; records unchanged')
