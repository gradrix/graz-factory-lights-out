"""Read-only local persisted arm audit: no candidate imports, commands, or endpoints."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib,json,statistics,stat,zlib,sqlite3
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ARM=ROOT/'.gflo/planning-trial-1/3-config-preview-decomposed'
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
ledger=load(ARM/'budget.json');result=load(ARM/'result.json');spec=load(ARM/'spec.json');manifest=load(OUT/'fixture-manifest.json');expected=load(OUT/'serving-lifecycle/expected-identity.json');binding=load(OUT/'environment-bindings.json')['python-api']
assert sha(OUT/'fixture-manifest.json')==spec['manifest_sha256']
assert ledger['limit']==48 and len(ledger['calls'])==48 and [r['number'] for r in ledger['calls']]==list(range(1,49))
assert {p.name for p in (ARM/'requests').iterdir()}=={f'{i:02d}' for i in range(1,49)}
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
runids=['ba6255bd4d74','300151e5e413'];children={};child_checks=[]
assert not (ARM/'factory/state.sqlite-wal').exists()
connection=sqlite3.connect('file:'+str((ARM/'factory/state.sqlite').resolve())+'?mode=ro&immutable=1',uri=True);connection.row_factory=sqlite3.Row
states={row['id']:dict(row) for row in connection.execute('SELECT id,status,attempts,message,contract_hash FROM runs')};connection.close()
for index,runid in enumerate(runids,1):
 run=ARM/'factory'/runid;task=load(run/'task.json');state=states[runid]
 expected_checks=manifest['cases'][1]['milestone_checks' if index==1 else 'full_checks']
 assert task['environment']==binding and task['checks']==expected_checks
 assert task['max_attempts']==3 and task['max_turns']==24 and task['review_required'] is True and state['attempts']==1
 assert state['contract_hash']==sha(run/'task.json')
 assert all(sha(run/'workspace'/name)==wanted for name,wanted in task['environment_inputs'].items())
 if index==1:
  accepted=load(run/'accepted.json');child=load(ARM/'child-1-result.json')
  assert child['environment']==binding and state['status']=='accepted' and child['contract_hash']==state['contract_hash']
  assert accepted['candidate']==fingerprint(run/'workspace') and accepted['patch_sha256']==sha(run/'change.patch')
  assert all(sha(run/path)==h for path,h in accepted['artifacts'].items())
 else:
  assert state['status']=='interrupted' and state['message']=='Shared completion request budget exhausted'
  assert not (run/'accepted.json').exists()
  child={'workspace':load(ARM/'child-1-result.json')['workspace'].replace(runids[0],runid),'directory':load(ARM/'child-1-result.json')['directory'].replace(runids[0],runid)}
 assert fingerprint(run/'acceptance')==task['acceptance_hash']
 for f in (run/'acceptance').rglob('*'):
  if f.is_file():assert sha(f)==manifest['files'][manifest['cases'][1]['acceptance']+'/'+str(f.relative_to(run/'acceptance'))]
 children[child['workspace']]=child
 child_checks.append({'run_id':runid,'status':state['status'],'attempts':state['attempts'],'checks':task['checks'],'observed_workspace_fingerprint':fingerprint(run/'workspace'),'contract_sha256':state['contract_hash']})
assert load(ARM/'children.json')==runids
failure=load(ARM/'child-result.json');assert failure==result['child']=={'status':'failed','error_type':'RuntimeError','error':'Shared completion request budget exhausted'}
assert result['status']=='failed' and result['exit_code']==1 and result['integrity_confirmed'] is False
assert load(ARM/'factory'/runids[1]/'attempts/1/interruption.json')=={'error':'Shared completion request budget exhausted','type':'RuntimeError'}
assert not (ARM/'final-verification.json').exists() and not (ARM/'final-review.json').exists() and not (ARM/'child-2-result.json').exists()
trajectory=[json.loads(line) for line in (ARM/'factory'/runids[1]/'attempts/1/trajectory.jsonl').read_text().splitlines()]
assert sum(x['event']=='request' for x in trajectory)==22 and sum(x['event']=='response' for x in trajectory)==21 and trajectory[-1]['event']=='request' and trajectory[-1]['turn']==22
final=None
plan=load(ARM/'plan.json');review=load(ARM/'plan-review.json');checkpoint=load(ARM/'checkpoint.json');restoration=load(ARM/'handoff-restoration.json');prior=ARM/'factory'/runids[0];second=ARM/'factory'/runids[1]
assert len(plan['tasks'])==2 and plan['tasks'][0]['id']=='task1' and plan['tasks'][1]['id']=='task2' and plan['tasks'][0]['depends_on']==[] and plan['tasks'][1]['depends_on']==['task1']
assert set(plan['tasks'][0]['requirement_ids'])==set(manifest['cases'][1]['milestone_requirement_ids'])
assert set(sum([x['requirement_ids'] for x in plan['tasks']],[]))=={x['id'] for x in manifest['cases'][1]['requirements']}
assert all(set(x)=={'id','objective','requirement_ids','depends_on'} for x in plan['tasks']) and review['decision']=='pass'
assert json.loads(load(ARM/'requests/01/response.json')['choices'][0]['message']['content'])==plan
assert json.loads(load(ARM/'requests/02/response.json')['choices'][0]['message']['content'])==review
public=json.loads(load(ARM/'requests/01/request.json')['messages'][1]['content']);review_public=json.loads(load(ARM/'requests/02/request.json')['messages'][1]['content'])
assert review_public==dict(public,plan=plan)
assert public['requirements']==manifest['cases'][1]['requirements'] and public['milestone_requirement_ids']==manifest['cases'][1]['milestone_requirement_ids']
fixture_task=ROOT.parent/'gflo-planning-prototype/evaluations/planning-pilot'/manifest['cases'][1]['task'];assert sha(fixture_task)==manifest['files'][manifest['cases'][1]['task']]
original_objective=load(fixture_task)['objective'];assert public['objective'].startswith(original_objective)
for index,runid in enumerate(runids):
 objective=load(ARM/'factory'/runid/'task.json')['objective'];assert objective.startswith(public['objective']) and json.dumps(plan['tasks'][index]) in objective
for name,content in public['files'].items():assert hashlib.sha256(content.encode()).hexdigest()==manifest['files'][manifest['cases'][1]['source']+'/'+name]
assert len(public['files'])==sum(k.startswith(manifest['cases'][1]['source']+'/') for k in manifest['files'])
assert checkpoint['run_id']==runids[0] and checkpoint['candidate']==child_checks[0]['observed_workspace_fingerprint'] and checkpoint['patch_sha256']==sha(prior/'change.patch')
for source in [prior/'workspace',ARM/'checkpoint']:
 actual={str(p.relative_to(source)):stat.S_IMODE(p.lstat().st_mode) for p in source.rglob('*') if '.git' not in p.relative_to(source).parts}
 assert actual==checkpoint['modes']
 for name in actual:
  p=source/name;assert not p.is_symlink()
  if p.is_file():assert p.read_bytes()==(prior/'workspace'/name).read_bytes()
assert restoration['after']==checkpoint['candidate'] and restoration['before']!=restoration['after']
assert restoration['mode_map_sha256']==hashlib.sha256(encoded(checkpoint['modes'])).hexdigest() and restoration['base_sha256']==sha(second/'base.json')
assert restoration['git_tree']==load(second/'base.json')['tree'] and load(second/'task.json')['base_commit']==checkpoint['commit']
obj=checkpoint['commit'];raw=zlib.decompress((ARM/'checkpoint/.git/objects'/obj[:2]/obj[2:]).read_bytes());assert hashlib.sha1(raw).hexdigest()==obj
commitbody=raw.split(b'\0',1)[1];assert commitbody.splitlines()[0].decode()=='tree '+restoration['git_tree']
head=(ARM/'checkpoint/.git/HEAD').read_text().strip();assert head.startswith('ref: ') and (ARM/'checkpoint/.git'/head[5:]).read_text().strip()==obj
creation=[]
for p in sorted((ARM/'executor-creation').iterdir()):
 fact=load(p);host=fact['host'];assert fact['image']==binding['image'];assert host['Runtime']=='runc' and host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True and host['CapDrop']==['ALL'] and host['SecurityOpt']==['no-new-privileges']
 assert host['Memory']==host['MemorySwap']==1073741824 and host['NanoCpus']==2000000000 and host['PidsLimit']==128 and host['ShmSize']==16777216
 assert not host['Devices'] and not host['DeviceRequests'];assert fact['config']['User']=='1000:1000'
 mounts={m['Destination']:m for m in fact['mounts']};assert len(mounts)==len(fact['mounts']) and set(mounts) in ({'/workspace','/opt/deps'},{'/workspace','/opt/deps','/acceptance'})
 assert mounts['/workspace']['Source'] in children and mounts['/opt/deps']['RW'] is False and mounts['/opt/deps']['Source']==binding['store']+'/'+binding['id']+'/deps'
 if '/acceptance' in mounts:assert mounts['/acceptance']['RW'] is False and mounts['/workspace']['RW'] is False and mounts['/acceptance']['Source']==children[mounts['/workspace']['Source']]['directory']+'/acceptance'
 assert all(m['Type']=='bind' for m in fact['mounts'])
 creation.append({'file':p.name,'name':fact['name'],'sha256':sha(p),'acceptance_mount':'/acceptance' in mounts})
assert len({x['name'] for x in creation})==len(creation)==53
assert not (ARM/'executor-uncertain.json').exists()
assert result['cleanup_confirmed'] is True and result['client_group_absent'] is True and result['idle_confirmed'] is True and all(x['confirmed_absent'] is True for x in result['cleanup'])
assert {x['workspace_label'] for x in result['cleanup']}=={hashlib.sha256(path.encode()).hexdigest() for path in children}
progress=[json.loads(x) for x in (ARM/'progress.jsonl').read_text().splitlines()];reserved=[x for x in progress if x['event']=='completion_reserved'];assert [x['number'] for x in reserved]==list(range(1,49)) and [x['role'] for x in reserved]==[x['role'] for x in ledger['calls']]
probes=[x for x in progress if x['event']=='serving_probe'];assert len(probes)==4 and all(x['identity']==expected and x['state']=='idle' and x['slots']==[{'id':0,'n_ctx':98304,'is_processing':False}] for x in probes)
gaps=[(datetime.fromisoformat(probes[j]['utc'])-datetime.fromisoformat(probes[i]['utc'])).total_seconds() for i,j in [(0,1),(2,3)]];assert min(gaps)>=1
assert result['work_elapsed_s']<1800 and result['cleanup_elapsed_s']<150 and result['work_finished_before_deadline'] is True and result['stop'] is None
assert {str(p.relative_to(ARM)):sha(p) for p in files}==before
seconds=[r['elapsed_s'] for r in rows]
audit={'outcome':'PASS_accounting_and_boundary_readback','arm_outcome':'failed','final_acceptance':False,'arm':ARM.name,'run_ids':runids,'child_checks':child_checks,'plan_requirement_coverage_verified':True,'checkpoint':checkpoint,'restoration':restoration,'milestone_accepted_candidate':accepted['candidate'],'final_candidate_status':'unaccepted_partial_workspace','request_count':len(rows),'request_limit':48,'roles':dict(roles),'all48_raw_pairs_complete_and_hash_consistent':True,'budget_failure':failure,'durable_child_states':states,'no49thtransport':'48reservations+48rawcapturepairs+frozenpretransportdenial; uncharged planned request22 in task2 trajectory','usage_reported_totals':dict(usage),'usage_missing_call_counts':{k:missing[k] for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens']},'finish_reasons':dict(finishes),'latency':{'work_s':result['work_elapsed_s'],'cleanup_s':result['cleanup_elapsed_s'],'sum_reported_request_elapsed_s':sum(seconds),'minimum_request_s':min(seconds),'median_request_s':statistics.median(seconds),'maximum_request_s':max(seconds)},'environment':binding,'executor_creation_count':len(creation),'executor_acceptance_mount_count':sum(x['acceptance_mount'] for x in creation),'executor_creation':creation,'serving_observation_count':len(probes),'serving_identity':expected,'serving_idle_pair_gaps_s':gaps,'fixed_checks':task['checks'],'final_verification':final,'source_files_unchanged':True,'reviewed_file_count':len(files),'request_rows':rows,'primary_hashes':{name:before[name] for name in ['budget.json','result.json','progress.jsonl','spec.json','factory/'+runid+'/task.json','factory/'+runids[0]+'/accepted.json','checkpoint.json','handoff-restoration.json','plan.json','plan-review.json']}}
prefix=manifest['cases'][1]['source']+'/'
source_expected={k[len(prefix):]:v for k,v in manifest['files'].items() if k.startswith(prefix)}
source_observed={str(p.relative_to(ARM/'source')):sha(p) for p in (ARM/'source').rglob('*') if p.is_file() and '.git' not in p.relative_to(ARM/'source').parts}
assert source_expected==source_observed
audit.update(original_source_matches_frozen_fixture=True,original_source_file_count=len(source_expected),request_max_raw_bytes=max(x['files']['request.body']['bytes'] for x in rows),response_max_raw_bytes=max(x['files']['response.body']['bytes'] for x in rows))
worker=load(ARM/'factory'/runids[0]/'attempts/1/worker.json')
assert worker['turns']==24 and worker['limited'] is True
assert [x['role'] for x in ledger['calls']]==['planner','plan_review']+['implementation']*24+['code_review']+['implementation']*21
audit.update(worker_turns=[{'run_id':runids[0],'turns':24,'limited':True,'summary_status':'turn_budget_exhausted'},{'run_id':runids[1],'returned_turns':21,'denied_planned_turn':22,'summary_status':'no_worker_result_budget_exception'}],request_allocation={'planner':[1],'plan_review':[2],'task1_implementation':[3,26],'task1_review':[27],'task2_implementation':[28,48],'task2_review':[],'final_full_review':[]},actual_mode_restoration_changed_fingerprint=True)
(OUT/'arm3-accounting.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k in ['outcome','request_count','roles','usage_reported_totals','usage_missing_call_counts','latency','executor_creation_count','executor_acceptance_mount_count','reviewed_file_count']},indent=2))
