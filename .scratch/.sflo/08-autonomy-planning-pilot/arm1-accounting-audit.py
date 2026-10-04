"""Read-only local persisted arm audit: no candidate imports, commands, or endpoints."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib,json,statistics,stat
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ARM=ROOT/'.gflo/planning-trial-1/1-manifest-reconcile-direct'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def fingerprint(root):
 h=hashlib.sha256()
 for p in sorted(root.rglob('*')):
  rel=str(p.relative_to(root));h.update(rel.encode()+b'\0');assert not p.is_symlink()
  if p.is_file():h.update(str(p.stat().st_mode & 0o777).encode()+b'\0');h.update(p.read_bytes())
  else:assert p.is_dir()
 return h.hexdigest()
files=[p for p in ARM.rglob('*') if p.is_file() and not p.is_symlink()]
before={str(p.relative_to(ARM)):sha(p) for p in files}
ledger=load(ARM/'budget.json');result=load(ARM/'result.json');spec=load(ARM/'spec.json');manifest=load(OUT/'fixture-manifest.json');expected=load(OUT/'serving-lifecycle/expected-identity.json');binding=load(OUT/'environment-bindings.json')['python-stdlib']
assert sha(OUT/'fixture-manifest.json')==spec['manifest_sha256']
assert ledger['limit']==48 and len(ledger['calls'])==23 and [r['number'] for r in ledger['calls']]==list(range(1,24))
assert {p.name for p in (ARM/'requests').iterdir()}=={f'{i:02d}' for i in range(1,24)}
rows=[];usage=Counter();missing=Counter();finishes=Counter();roles=Counter()
for call in ledger['calls']:
 folder=ARM/'requests'/f"{call['number']:02d}";assert {p.name for p in folder.iterdir()}=={'request.json','response.json','request.body','response.body','transport.json'}
 request=load(folder/'request.json');response=load(folder/'response.json');transport=load(folder/'transport.json')
 assert hashlib.sha256(encoded(request)).hexdigest()==call['request_sha256']
 assert hashlib.sha256(encoded(response)).hexdigest()==call['response_sha256']
 assert load(folder/'request.body')==request and load(folder/'response.body')==response
 assert call['status']=='returned' and transport=={'http_status':200,'complete':True,'bytes_captured':(folder/'response.body').stat().st_size}
 assert (folder/'request.json').stat().st_size<=4*1024*1024 and (folder/'response.body').stat().st_size<=1024*1024
 assert request['model']=='flash-next-coder' and request['temperature']==0 and request['max_tokens']==4096 and request['reasoning_effort']=='medium' and request['thinking_budget_tokens']==1024 and request['chat_template_kwargs']=={'enable_thinking':True}
 assert response['usage']==call['usage'];roles[call['role']]+=1
 fields={k:response['usage'].get(k) for k in ['prompt_tokens','completion_tokens','total_tokens']};fields['cached_prompt_tokens']=response['usage'].get('prompt_tokens_details',{}).get('cached_tokens')
 for name,value in fields.items():
  if value is None:missing[name]+=1
  else:assert type(value) is int and value>=0;usage[name]+=value
 if call['role']=='implementation':assert {x['function']['name'] for x in request['tools']}=={'run','check','question'}
 else:assert 'tools' not in request and 'functions' not in request
 finishes.update(c.get('finish_reason','missing') for c in response.get('choices',[]))
 rows.append({'number':call['number'],'role':call['role'],'elapsed_s':call['elapsed_s'],'usage':fields,'response_model':response['model'],'finish_reason':[x.get('finish_reason') for x in response['choices']],'timings':response.get('timings'),'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(folder.iterdir())}})
runid='b420f7770b76';run=ARM/'factory'/runid;task=load(run/'task.json');accepted=load(run/'accepted.json');child=load(ARM/'child-1-result.json')
assert task['environment']==binding and child['environment']==binding and task['checks']==manifest['cases'][0]['full_checks']
assert task['max_attempts']==3 and task['max_turns']==24 and task['review_required'] is True and child['attempts']==1
assert child['contract_hash']==sha(run/'task.json') and accepted['candidate']==result['child']['candidate']==fingerprint(run/'workspace')
assert accepted['patch_sha256']==sha(run/'change.patch') and all(sha(run/path)==h for path,h in accepted['artifacts'].items())
assert fingerprint(run/'acceptance')==task['acceptance_hash']
for p in (run/'acceptance').rglob('*'):
 if p.is_file():assert sha(p)==manifest['files'][manifest['cases'][0]['acceptance']+'/'+str(p.relative_to(run/'acceptance'))]
final=load(ARM/'final-verification.json');assert final['passed'] is True and final['checks'][0]['command']==task['checks'][0] and all(x['exit_code']==0 and x['image']==binding['image'] for x in final['checks'])
creation=[]
for p in sorted((ARM/'executor-creation').iterdir()):
 fact=load(p);host=fact['host'];assert fact['image']==binding['image'];assert host['Runtime']=='runc' and host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True and host['CapDrop']==['ALL'] and host['SecurityOpt']==['no-new-privileges']
 assert host['Memory']==host['MemorySwap']==1073741824 and host['NanoCpus']==2000000000 and host['PidsLimit']==128 and host['ShmSize']==16777216
 assert not host['Devices'] and not host['DeviceRequests'];assert fact['config']['User']=='1000:1000'
 mounts={m['Destination']:m for m in fact['mounts']};assert len(mounts)==len(fact['mounts']) and set(mounts) in ({'/workspace','/opt/deps'},{'/workspace','/opt/deps','/acceptance'})
 assert mounts['/workspace']['Source']==child['workspace'] and mounts['/opt/deps']['RW'] is False and mounts['/opt/deps']['Source']==binding['store']+'/'+binding['id']+'/deps'
 if '/acceptance' in mounts:assert mounts['/acceptance']['RW'] is False and mounts['/workspace']['RW'] is False and mounts['/acceptance']['Source']==child['directory']+'/acceptance'
 assert all(m['Type']=='bind' for m in fact['mounts'])
 creation.append({'file':p.name,'name':fact['name'],'sha256':sha(p),'acceptance_mount':'/acceptance' in mounts})
assert len({x['name'] for x in creation})==len(creation)==25
assert not (ARM/'executor-uncertain.json').exists()
assert result['cleanup_confirmed'] is True and result['client_group_absent'] is True and result['idle_confirmed'] is True and all(x['confirmed_absent'] is True for x in result['cleanup'])
assert result['cleanup'][0]['workspace_label']==hashlib.sha256(child['workspace'].encode()).hexdigest()
progress=[json.loads(x) for x in (ARM/'progress.jsonl').read_text().splitlines()];reserved=[x for x in progress if x['event']=='completion_reserved'];assert [x['number'] for x in reserved]==list(range(1,24)) and [x['role'] for x in reserved]==[x['role'] for x in ledger['calls']]
probes=[x for x in progress if x['event']=='serving_probe'];assert len(probes)==4 and all(x['identity']==expected and x['state']=='idle' and x['slots']==[{'id':0,'n_ctx':98304,'is_processing':False}] for x in probes)
gaps=[(datetime.fromisoformat(probes[j]['utc'])-datetime.fromisoformat(probes[i]['utc'])).total_seconds() for i,j in [(0,1),(2,3)]];assert min(gaps)>=1
assert result['work_elapsed_s']<1800 and result['cleanup_elapsed_s']<150 and result['work_finished_before_deadline'] is True and result['stop'] is None
assert {str(p.relative_to(ARM)):sha(p) for p in files}==before
seconds=[r['elapsed_s'] for r in rows]
audit={'outcome':'PASS_accounting_and_boundary_readback','arm':ARM.name,'run_id':runid,'candidate':accepted['candidate'],'request_count':len(rows),'request_limit':48,'roles':dict(roles),'all23_raw_pairs_complete_and_hash_consistent':True,'usage_reported_totals':dict(usage),'usage_missing_call_counts':{k:missing[k] for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens']},'finish_reasons':dict(finishes),'latency':{'work_s':result['work_elapsed_s'],'cleanup_s':result['cleanup_elapsed_s'],'sum_reported_request_elapsed_s':sum(seconds),'minimum_request_s':min(seconds),'median_request_s':statistics.median(seconds),'maximum_request_s':max(seconds)},'environment':binding,'executor_creation_count':len(creation),'executor_acceptance_mount_count':sum(x['acceptance_mount'] for x in creation),'executor_creation':creation,'serving_observation_count':len(probes),'serving_identity':expected,'serving_idle_pair_gaps_s':gaps,'fixed_checks':task['checks'],'final_verification':final,'source_files_unchanged':True,'reviewed_file_count':len(files),'request_rows':rows,'primary_hashes':{name:before[name] for name in ['budget.json','result.json','progress.jsonl','spec.json','final-verification.json','final-review.json','factory/'+runid+'/task.json','factory/'+runid+'/accepted.json']}}
prefix=manifest['cases'][0]['source']+'/'
source_expected={k[len(prefix):]:v for k,v in manifest['files'].items() if k.startswith(prefix)}
source_observed={str(p.relative_to(ARM/'source')):sha(p) for p in (ARM/'source').rglob('*') if p.is_file() and '.git' not in p.relative_to(ARM/'source').parts}
assert source_expected==source_observed
audit.update(original_source_matches_frozen_fixture=True,original_source_file_count=len(source_expected),request_max_raw_bytes=max(x['files']['request.body']['bytes'] for x in rows),response_max_raw_bytes=max(x['files']['response.body']['bytes'] for x in rows))
(OUT/'arm1-accounting.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k in ['outcome','request_count','roles','usage_reported_totals','usage_missing_call_counts','latency','executor_creation_count','executor_acceptance_mount_count','reviewed_file_count']},indent=2))
