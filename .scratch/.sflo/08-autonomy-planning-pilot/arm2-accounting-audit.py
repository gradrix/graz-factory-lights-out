"""Read-only local persisted arm audit: no candidate imports, commands, or endpoints."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib,json,statistics,stat,zlib
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ARM=ROOT/'.gflo/planning-trial-1/2-manifest-reconcile-decomposed'
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
assert ledger['limit']==48 and len(ledger['calls'])==36 and [r['number'] for r in ledger['calls']]==list(range(1,37))
assert {p.name for p in (ARM/'requests').iterdir()}=={f'{i:02d}' for i in range(1,37)}
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
runids=['b90b66156d7f','037a513a8192'];children={};child_checks=[]
for index,runid in enumerate(runids,1):
 run=ARM/'factory'/runid;task=load(run/'task.json');accepted=load(run/'accepted.json');child=load(ARM/f'child-{index}-result.json')
 expected_checks=manifest['cases'][0]['milestone_checks' if index==1 else 'full_checks']
 assert task['environment']==binding and child['environment']==binding and task['checks']==expected_checks
 assert task['max_attempts']==3 and task['max_turns']==24 and task['review_required'] is True and child['attempts']==1
 assert child['contract_hash']==sha(run/'task.json') and accepted['candidate']==fingerprint(run/'workspace')
 assert accepted['patch_sha256']==sha(run/'change.patch') and all(sha(run/path)==h for path,h in accepted['artifacts'].items())
 assert fingerprint(run/'acceptance')==task['acceptance_hash']
 for f in (run/'acceptance').rglob('*'):
  if f.is_file():assert sha(f)==manifest['files'][manifest['cases'][0]['acceptance']+'/'+str(f.relative_to(run/'acceptance'))]
 children[child['workspace']]=child
 child_checks.append({'run_id':runid,'attempts':child['attempts'],'checks':task['checks'],'candidate':accepted['candidate'],'contract_sha256':child['contract_hash']})
assert result['child']['children']==runids and result['child']['candidate']==accepted['candidate']
final=load(ARM/'final-verification.json');assert final['passed'] is True and final['checks'][0]['command']==task['checks'][0] and all(x['exit_code']==0 and x['image']==binding['image'] for x in final['checks'])
plan=load(ARM/'plan.json');review=load(ARM/'plan-review.json');checkpoint=load(ARM/'checkpoint.json');restoration=load(ARM/'handoff-restoration.json');prior=ARM/'factory'/runids[0];second=ARM/'factory'/runids[1]
assert len(plan['tasks'])==2 and plan['tasks'][0]['id']=='task1' and plan['tasks'][1]['id']=='task2' and plan['tasks'][0]['depends_on']==[] and plan['tasks'][1]['depends_on']==['task1']
assert set(plan['tasks'][0]['requirement_ids'])==set(manifest['cases'][0]['milestone_requirement_ids'])
assert set(sum([x['requirement_ids'] for x in plan['tasks']],[]))=={x['id'] for x in manifest['cases'][0]['requirements']}
assert all(set(x)=={'id','objective','requirement_ids','depends_on'} for x in plan['tasks']) and review['decision']=='pass'
assert json.loads(load(ARM/'requests/01/response.json')['choices'][0]['message']['content'])==plan
assert json.loads(load(ARM/'requests/02/response.json')['choices'][0]['message']['content'])==review
public=json.loads(load(ARM/'requests/01/request.json')['messages'][1]['content']);review_public=json.loads(load(ARM/'requests/02/request.json')['messages'][1]['content'])
assert review_public==dict(public,plan=plan)
assert public['requirements']==manifest['cases'][0]['requirements'] and public['milestone_requirement_ids']==manifest['cases'][0]['milestone_requirement_ids']
fixture_task=ROOT.parent/'gflo-planning-prototype/evaluations/planning-pilot'/manifest['cases'][0]['task'];assert sha(fixture_task)==manifest['files'][manifest['cases'][0]['task']]
original_objective=load(fixture_task)['objective'];assert public['objective'].startswith(original_objective)
for index,runid in enumerate(runids):
 objective=load(ARM/'factory'/runid/'task.json')['objective'];assert objective.startswith(public['objective']) and json.dumps(plan['tasks'][index]) in objective
for name,content in public['files'].items():assert hashlib.sha256(content.encode()).hexdigest()==manifest['files'][manifest['cases'][0]['source']+'/'+name]
assert len(public['files'])==8
assert checkpoint['run_id']==runids[0] and checkpoint['candidate']==child_checks[0]['candidate'] and checkpoint['patch_sha256']==sha(prior/'change.patch')
for source in [prior/'workspace',ARM/'checkpoint']:
 actual={str(p.relative_to(source)):stat.S_IMODE(p.lstat().st_mode) for p in source.rglob('*') if '.git' not in p.relative_to(source).parts}
 assert actual==checkpoint['modes']
 for name in actual:
  p=source/name;assert not p.is_symlink()
  if p.is_file():assert p.read_bytes()==(prior/'workspace'/name).read_bytes()
assert restoration['before']==restoration['after']==checkpoint['candidate']
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
assert len({x['name'] for x in creation})==len(creation)==37
assert not (ARM/'executor-uncertain.json').exists()
assert result['cleanup_confirmed'] is True and result['client_group_absent'] is True and result['idle_confirmed'] is True and all(x['confirmed_absent'] is True for x in result['cleanup'])
assert {x['workspace_label'] for x in result['cleanup']}=={hashlib.sha256(path.encode()).hexdigest() for path in children}
progress=[json.loads(x) for x in (ARM/'progress.jsonl').read_text().splitlines()];reserved=[x for x in progress if x['event']=='completion_reserved'];assert [x['number'] for x in reserved]==list(range(1,37)) and [x['role'] for x in reserved]==[x['role'] for x in ledger['calls']]
probes=[x for x in progress if x['event']=='serving_probe'];assert len(probes)==4 and all(x['identity']==expected and x['state']=='idle' and x['slots']==[{'id':0,'n_ctx':98304,'is_processing':False}] for x in probes)
gaps=[(datetime.fromisoformat(probes[j]['utc'])-datetime.fromisoformat(probes[i]['utc'])).total_seconds() for i,j in [(0,1),(2,3)]];assert min(gaps)>=1
assert result['work_elapsed_s']<1800 and result['cleanup_elapsed_s']<150 and result['work_finished_before_deadline'] is True and result['stop'] is None
assert {str(p.relative_to(ARM)):sha(p) for p in files}==before
seconds=[r['elapsed_s'] for r in rows]
audit={'outcome':'PASS_accounting_and_boundary_readback','arm':ARM.name,'run_ids':runids,'child_checks':child_checks,'plan_requirement_coverage_verified':True,'checkpoint':checkpoint,'restoration':restoration,'candidate':accepted['candidate'],'request_count':len(rows),'request_limit':48,'roles':dict(roles),'all36_raw_pairs_complete_and_hash_consistent':True,'usage_reported_totals':dict(usage),'usage_missing_call_counts':{k:missing[k] for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens']},'finish_reasons':dict(finishes),'latency':{'work_s':result['work_elapsed_s'],'cleanup_s':result['cleanup_elapsed_s'],'sum_reported_request_elapsed_s':sum(seconds),'minimum_request_s':min(seconds),'median_request_s':statistics.median(seconds),'maximum_request_s':max(seconds)},'environment':binding,'executor_creation_count':len(creation),'executor_acceptance_mount_count':sum(x['acceptance_mount'] for x in creation),'executor_creation':creation,'serving_observation_count':len(probes),'serving_identity':expected,'serving_idle_pair_gaps_s':gaps,'fixed_checks':task['checks'],'final_verification':final,'source_files_unchanged':True,'reviewed_file_count':len(files),'request_rows':rows,'primary_hashes':{name:before[name] for name in ['budget.json','result.json','progress.jsonl','spec.json','final-verification.json','final-review.json','factory/'+runid+'/task.json','factory/'+runid+'/accepted.json','checkpoint.json','handoff-restoration.json','plan.json','plan-review.json']}}
prefix=manifest['cases'][0]['source']+'/'
source_expected={k[len(prefix):]:v for k,v in manifest['files'].items() if k.startswith(prefix)}
source_observed={str(p.relative_to(ARM/'source')):sha(p) for p in (ARM/'source').rglob('*') if p.is_file() and '.git' not in p.relative_to(ARM/'source').parts}
assert source_expected==source_observed
audit.update(original_source_matches_frozen_fixture=True,original_source_file_count=len(source_expected),request_max_raw_bytes=max(x['files']['request.body']['bytes'] for x in rows),response_max_raw_bytes=max(x['files']['response.body']['bytes'] for x in rows))
workers=[load(ARM/'factory'/rid/'attempts/1/worker.json') for rid in runids]
assert workers[0]['turns']==7 and workers[1]['turns']==24 and workers[1]['limited'] is True
assert [x['role'] for x in ledger['calls']]==['planner','plan_review']+['implementation']*7+['code_review']+['implementation']*24+['code_review']*2
audit.update(worker_turns=[{'run_id':rid,'turns':w['turns'],'limited':w.get('limited',False),'finish_reason':w.get('finish_reason'),'summary_status':'turn_budget_exhausted' if w.get('limited') else 'normal_stop'} for rid,w in zip(runids,workers)],request_allocation={'planner':[1],'plan_review':[2],'task1_implementation':[3,9],'task1_review':[10],'task2_implementation':[11,34],'task2_review':[35],'final_full_review':[36]},actual_mode_restoration_changed_fingerprint=restoration['before']!=restoration['after'])
(OUT/'arm2-accounting.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k in ['outcome','request_count','roles','usage_reported_totals','usage_missing_call_counts','latency','executor_creation_count','executor_acceptance_mount_count','reviewed_file_count']},indent=2))
