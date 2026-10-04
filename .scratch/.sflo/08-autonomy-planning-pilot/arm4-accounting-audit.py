"""Read-only local persisted arm audit: no candidate imports, commands, or endpoints."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib,json,statistics,stat,zlib,sqlite3
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ARM=ROOT/'.gflo/planning-trial-1/4-config-preview-direct'
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
runids=['a8aac6d4726e'];children={};child_checks=[]
assert not (ARM/'factory/state.sqlite-wal').exists()
connection=sqlite3.connect('file:'+str((ARM/'factory/state.sqlite').resolve())+'?mode=ro&immutable=1',uri=True);connection.row_factory=sqlite3.Row
states={row['id']:dict(row) for row in connection.execute('SELECT id,status,attempts,message,contract_hash FROM runs')};connection.close()
runid=runids[0];run=ARM/'factory'/runid;task=load(run/'task.json');state=states[runid]
assert task['environment']==binding and task['checks']==manifest['cases'][1]['full_checks']
assert task['max_attempts']==3 and task['max_turns']==24 and task['review_required'] is True and state['attempts']==3
assert state['contract_hash']==sha(run/'task.json') and state['status']=='interrupted' and state['message']=='Shared completion request budget exhausted'
assert all(sha(run/'workspace'/name)==wanted for name,wanted in task['environment_inputs'].items())
assert not (run/'accepted.json').exists()
remote=task['repo'].rsplit('/',1)[0]+'/factory/'+runid
child={'workspace':remote+'/workspace','directory':remote};children[child['workspace']]=child
assert fingerprint(run/'acceptance')==task['acceptance_hash']
for f in (run/'acceptance').rglob('*'):
 if f.is_file():assert sha(f)==manifest['files'][manifest['cases'][1]['acceptance']+'/'+str(f.relative_to(run/'acceptance'))]
child_checks.append({'run_id':runid,'status':state['status'],'attempts':state['attempts'],'checks':task['checks'],'observed_workspace_fingerprint':fingerprint(run/'workspace'),'contract_sha256':state['contract_hash']})
assert load(ARM/'children.json')==runids
failure=load(ARM/'child-result.json');assert failure==result['child']=={'status':'failed','error_type':'RuntimeError','error':'Shared completion request budget exhausted'}
assert result['status']=='failed' and result['exit_code']==1 and result['integrity_confirmed'] is False
assert load(run/'attempts/3/interruption.json')=={'error':'Shared completion request budget exhausted','type':'RuntimeError'}
assert not (ARM/'final-verification.json').exists() and not (ARM/'final-review.json').exists() and not (ARM/'child-1-result.json').exists()
assert not (ARM/'checkpoint.json').exists() and not (ARM/'plan.json').exists()
attempts=[]
for number in [1,2,3]:
 folder=run/'attempts'/str(number);trace=[json.loads(line) for line in (folder/'trajectory.jsonl').read_text().splitlines()]
 requests=[x for x in trace if x['event']=='request'];responses=[x for x in trace if x['event']=='response']
 assert len(requests)==(24 if number<3 else 1) and len(responses)==(24 if number<3 else 0)
 info={'number':number,'planned_requests':len(requests),'returned_responses':len(responses)}
 if number<3:
  worker=load(folder/'worker.json');verification=load(folder/'verification.json');assert worker['turns']==24 and worker['limited'] is True and verification['passed'] is False
  assert verification['checks'][0]['command']==task['checks'][0] and verification['checks'][0]['exit_code']==1
  info.update(limited=True,verification_passed=False,check_exit_codes=[x['exit_code'] for x in verification['checks']])
 else:assert trace[-1]['event']=='request' and trace[-1]['turn']==1 and not (folder/'worker.json').exists()
 attempts.append(info)
fixture_task=ROOT.parent/'gflo-planning-prototype/evaluations/planning-pilot'/manifest['cases'][1]['task'];assert sha(fixture_task)==manifest['files'][manifest['cases'][1]['task']]
assert task['objective'].startswith(load(fixture_task)['objective'])
final=None
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
assert len({x['name'] for x in creation})==len(creation)==59
assert not (ARM/'executor-uncertain.json').exists()
assert result['cleanup_confirmed'] is True and result['client_group_absent'] is True and result['idle_confirmed'] is True and all(x['confirmed_absent'] is True for x in result['cleanup'])
assert {x['workspace_label'] for x in result['cleanup']}=={hashlib.sha256(path.encode()).hexdigest() for path in children}
progress=[json.loads(x) for x in (ARM/'progress.jsonl').read_text().splitlines()];reserved=[x for x in progress if x['event']=='completion_reserved'];assert [x['number'] for x in reserved]==list(range(1,49)) and [x['role'] for x in reserved]==[x['role'] for x in ledger['calls']]
probes=[x for x in progress if x['event']=='serving_probe'];assert len(probes)==4 and all(x['identity']==expected and x['state']=='idle' and x['slots']==[{'id':0,'n_ctx':98304,'is_processing':False}] for x in probes)
gaps=[(datetime.fromisoformat(probes[j]['utc'])-datetime.fromisoformat(probes[i]['utc'])).total_seconds() for i,j in [(0,1),(2,3)]];assert min(gaps)>=1
assert result['work_elapsed_s']<1800 and result['cleanup_elapsed_s']<150 and result['work_finished_before_deadline'] is True and result['stop'] is None
assert {str(p.relative_to(ARM)):sha(p) for p in files}==before
seconds=[r['elapsed_s'] for r in rows]
audit={'outcome':'PASS_accounting_and_boundary_readback','arm_outcome':'failed','final_acceptance':False,'arm':ARM.name,'run_ids':runids,'child_checks':child_checks,'final_candidate_status':'unaccepted_partial_workspace','request_count':len(rows),'request_limit':48,'roles':dict(roles),'all48_raw_pairs_complete_and_hash_consistent':True,'budget_failure':failure,'durable_child_states':states,'no49thtransport':'48reservations+48rawcapturepairs+frozenpretransportdenial; uncharged planned attempt3 turn1','usage_reported_totals':dict(usage),'usage_missing_call_counts':{k:missing[k] for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens']},'finish_reasons':dict(finishes),'latency':{'work_s':result['work_elapsed_s'],'cleanup_s':result['cleanup_elapsed_s'],'sum_reported_request_elapsed_s':sum(seconds),'minimum_request_s':min(seconds),'median_request_s':statistics.median(seconds),'maximum_request_s':max(seconds)},'environment':binding,'executor_creation_count':len(creation),'executor_acceptance_mount_count':sum(x['acceptance_mount'] for x in creation),'executor_creation':creation,'serving_observation_count':len(probes),'serving_identity':expected,'serving_idle_pair_gaps_s':gaps,'fixed_checks':task['checks'],'final_verification':final,'source_files_unchanged':True,'reviewed_file_count':len(files),'request_rows':rows,'primary_hashes':{name:before[name] for name in ['budget.json','result.json','progress.jsonl','spec.json','factory/'+runid+'/task.json','factory/'+runid+'/attempts/3/interruption.json']}}
prefix=manifest['cases'][1]['source']+'/'
source_expected={k[len(prefix):]:v for k,v in manifest['files'].items() if k.startswith(prefix)}
source_observed={str(p.relative_to(ARM/'source')):sha(p) for p in (ARM/'source').rglob('*') if p.is_file() and '.git' not in p.relative_to(ARM/'source').parts}
assert source_expected==source_observed
audit.update(original_source_matches_frozen_fixture=True,original_source_file_count=len(source_expected),request_max_raw_bytes=max(x['files']['request.body']['bytes'] for x in rows),response_max_raw_bytes=max(x['files']['response.body']['bytes'] for x in rows))
assert [x['role'] for x in ledger['calls']]==['implementation']*48
audit.update(attempts=attempts,request_allocation={'attempt1_implementation':[1,24],'attempt2_implementation':[25,48],'attempt3_transports':[],'code_review':[],'final_full_review':[]})
trial=ARM.parent;download=load(OUT/'trial-download-integrity.json');artifact_manifest=load(OUT/'trial-artifact-hashes.json')
assert sha(OUT/'trial-artifact-hashes.json')==download['manifest_sha256']==sha(trial/'artifact-hashes.json')
assert len(artifact_manifest)==download['verified_file_count']==1334
for name,wanted in artifact_manifest.items():
 path=trial/name;assert path.resolve().is_relative_to(trial.resolve()) and path.is_file() and not path.is_symlink() and sha(path)==wanted
actual_set={str(p.relative_to(trial)) for p in trial.rglob('*') if p.is_file() and not p.is_symlink() and '.git' not in p.parts and p!=trial/'artifact-hashes.json'}
assert actual_set==set(artifact_manifest)
summary=load(trial/'results.json');experiment=load(trial/'experiment.json')
assert experiment['order']==[[0,'direct'],[0,'decomposed'],[1,'decomposed'],[1,'direct']] and experiment['requests_per_arm']==48 and experiment['work_seconds']==1800 and experiment['cleanup_seconds']==150
assert len(summary)==4 and [x['status'] for x in summary]==['accepted','accepted','failed','failed']
all_reports=[load(OUT/f'arm{i}-accounting.json') for i in [1,2,3]]+[audit]
for entry,report in zip(summary,all_reports):
 folder=trial/entry['arm'];assert load(folder/'result.json')==entry
 assert len(load(folder/'budget.json')['calls'])==report['request_count']
 assert {p.name for p in (folder/'requests').iterdir()}=={f'{n:02d}' for n in range(1,report['request_count']+1)}
 assert all(sha(folder/name)==wanted for name,wanted in report['primary_hashes'].items())
 assert entry['client_group_absent'] is True and entry['cleanup_confirmed'] is True and entry['idle_confirmed'] is True
 assert report['serving_identity']==expected
usage_totals={key:sum(x['usage_reported_totals'][key] for x in all_reports) for key in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens']}
role_totals=Counter()
for report in all_reports:role_totals.update(report['roles'])
audit['whole_run']={'artifact_manifest_sha256':download['manifest_sha256'],'verified_entries':1334,'actual_file_set_matches_excluding_git_metadata_and_manifest_itself':True,'per_arm_requests':[x['request_count'] for x in all_reports],'charged_project_requests':sum(x['request_count'] for x in all_reports),'roles':dict(role_totals),'usage_reported_totals':usage_totals,'all_usage_fields_reported':all(not any(x['usage_missing_call_counts'].values()) for x in all_reports),'sum_work_s':sum(x['latency']['work_s'] for x in all_reports),'sum_cleanup_s':sum(x['latency']['cleanup_s'] for x in all_reports),'sum_request_elapsed_s':sum(x['latency']['sum_reported_request_elapsed_s'] for x in all_reports),'factory_outcomes':[x['status'] for x in summary],'all_cleanup_and_idle_confirmed':True,'all_serving_identities_equal':True,'executor_creation_count':sum(x['executor_creation_count'] for x in all_reports),'separate_cancellation_probe_requests':1,'cancellation_probe_usage_not_available':True}
(OUT/'arm4-accounting.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k in ['outcome','request_count','roles','usage_reported_totals','usage_missing_call_counts','latency','executor_creation_count','executor_acceptance_mount_count','reviewed_file_count']},indent=2))
