#!/usr/bin/env python3
"""Read-only artifact audit: never imports/executes candidates or contacts services."""
import ast, collections, datetime, hashlib, json, statistics
from pathlib import Path

MAIN=Path(__file__).resolve().parent
REPO=MAIN.parents[2]
ROOT=REPO/'.gflo/executable-review-trial-1'
PROTO=Path('/home/gradrix/repos/gflo-review-prototype')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def facts(root):return {str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
def assignment(path,name):
 for node in ast.parse(path.read_text()).body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):return node.value
 raise AssertionError(name)
def countsum(usages,key):return sum(u[key] for u in usages) if all(type(u.get(key)) is int for u in usages) else None
before=facts(ROOT)
manifest=read(MAIN/'trial-artifact-hashes.json')
assert len(manifest)==325 and all(before[n]==v for n,v in manifest.items())
assert set(before)==set(manifest)|{'artifact-hashes.json'}
assert read(ROOT/'artifact-hashes.json')==manifest
assert read(MAIN/'trial-download-integrity.json')['manifest_sha256']==sha((MAIN/'trial-artifact-hashes.json').read_bytes())
admission=read(MAIN/'trial-1-admission.json');candidate=read(MAIN/'builder-candidate.json')
assert sha((MAIN/'trial-1-admission.json').read_bytes())==read(MAIN/'trial-1-process.json')['admission_sha256']
assert admission['prototype_commit']==candidate['prototype_commit']=='37b7f1d1416d5497ca38291b47b364882d2d44ef'
assert all(sha((PROTO/n).read_bytes())==v for n,v in {**candidate['source_sha256'],**candidate['reused_source_sha256']}.items())
assert all(sha((MAIN/n).read_bytes())==v for n,v in admission['gates_sha256'].items())
fixture=read(MAIN/'fixture-manifest.json');profile=read(ROOT/'experiment.json')['profile']
assert profile=={'model':'flash-next-coder','temperature':0,'max_tokens':4096,'reasoning_effort':'medium','thinking_budget_tokens':1024,'chat_template_kwargs':{'enable_thinking':True}}
review_system=ast.literal_eval(assignment(PROTO/'gflo/review.py','SYSTEM'))
system_ast=assignment(PROTO/'ops/executable_review_prototype.py','SYSTEM')
expected_system=review_system.replace(*[ast.literal_eval(v) for v in system_ast.left.args])+ast.literal_eval(system_ast.right)
for node in ast.parse((PROTO/'ops/executable_review_prototype.py').read_text()).body:
 if isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='SYSTEM':expected_system+=ast.literal_eval(node.value)
expected_tools=ast.literal_eval(assignment(PROTO/'ops/executable_review_prototype.py','TOOLS'))
identity=read(MAIN/'pretrial-idle.json')['identity']
results=read(ROOT/'results.json');assert results==read(MAIN/'trial-results.json')
assert [r['case'] for r in results]==admission['order']==['case-01','case-02','case-03','case-04']
cases=[];all_usage=[];all_request_times=[];names=set();all_commands=[]
for index,result in enumerate(results):
 case=ROOT/result['case'];ledger=read(case/'ledger.json');inp=read(case/'input.json');events=[json.loads(line) for line in (case/'progress.jsonl').read_text().splitlines()]
 assert result==read(case/'result.json') and result['child']==read(case/'child-result.json')
 assert ledger['request_limit']==8 and ledger['command_limit']==12 and len(ledger['requests'])<=8 and len(ledger['commands'])<=12
 assert [x['number'] for x in ledger['requests']]==list(range(1,len(ledger['requests'])+1))
 assert [x['number'] for x in ledger['commands']]==list(range(1,len(ledger['commands'])+1))
 for kind in ['requests','commands']:
  assert sorted(p.name for p in (case/kind).iterdir())==[f'{i:02d}' for i in range(1,len(ledger[kind])+1)]
  assert [e['number'] for e in events if e['event']==kind+'_reserved']==list(range(1,len(ledger[kind])+1))
 assert result['stop'] is None and result['work_finished_before_deadline'] is True and result['work_elapsed_s']<300
 assert result['cleanup_elapsed_s']<150 and all(result[k] is True for k in ['cleanup_confirmed','idle_confirmed','client_group_absent'])
 assert not (case/'executor-uncertain.json').exists()
 probes=[e for e in events if e['event']=='serving_probe'];assert len(probes)==4
 for e in probes:
  assert e['state']=='idle' and enc(e['identity'])==enc(identity)
  assert enc(e['slots'])==enc([{'id':0,'is_processing':False,'n_ctx':98304}])
 times=[datetime.datetime.fromisoformat(e['utc']) for e in probes]
 gaps=[(times[b]-times[a]).total_seconds() for a,b in [(0,1),(2,3)]];assert min(gaps)>=1
 assert events[0]==probes[0] and events[1]==probes[1] and events[-2:]==probes[2:]
 fixed=fixture['cases'][index];source=case/'candidate'
 expected={n.removeprefix(fixed['source']+'/'):v for n,v in fixture['files'].items() if n.startswith(fixed['source']+'/')}
 assert facts(source)==expected
 assert {n:f['sha256'] for n,f in inp['facts'].items() if f['type']=='file'}==expected
 assert inp['objective_sha256']==fixture['files'][fixed['objective']]
 for n,f in inp['facts'].items():assert f['mode']==fixture['modes'][fixed['source']+'/'+n]
 assert inp['source_root_mode']==fixture['modes'][fixed['source']]
 # Download mode preservation is separately measured, not presumed.
 copied_modes={n:(source/n).stat().st_mode & 0o777 for n in inp['facts']}
 copied_modes_match=all(copied_modes[n]==v['mode'] for n,v in inp['facts'].items())
 commands=[]
 for charge in ledger['commands']:
  d=case/'commands'/f"{charge['number']:02d}";cmd=read(d/'command.json');creation=read(d/'creation.json');start=read(d/'started.json');actual=read(d/'result.json');cleanup=read(d/'cleanup.json');stdout=(d/'stdout.body').read_bytes()
  assert charge['status']=='attested' and charge['name'] not in names;names.add(charge['name'])
  assert cmd['argv'][-1]==charge['command'] and 0<len(charge['command'])<=16384 and 0<cmd['timeout_s']<=60
  assert cmd['argv'][-2]==start['nonce'] and stdout.startswith((start['nonce']+'\n').encode())
  assert sha(stdout)==start['stdout_sha256']==charge['stdout_sha256'] and sha(actual['output'].encode())==charge['stderr_sha256']
  assert len(stdout)==actual['stdout_bytes'] and len(stdout)<=16384+len(start['nonce'])+1
  assert charge['exit_code']==actual['exit_code'] and charge['timed_out']==actual['timed_out'] is False and actual['limited'] is False
  assert creation['name']==cleanup['name']==charge['name'] and cleanup['confirmed_absent'] is True
  assert creation['image']=='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
  host=creation['host'];assert host['Runtime']=='runc' and host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True
  assert host['CapDrop']==['ALL'] and 'no-new-privileges' in host['SecurityOpt'] and not host['Devices'] and not host['DeviceRequests']
  for k,v in {'Memory':1073741824,'MemorySwap':1073741824,'NanoCpus':2000000000,'PidsLimit':128,'ShmSize':16777216,'Tmpfs':{'/tmp':'rw,nosuid,nodev,size=128m'}}.items():assert host[k]==v
  assert creation['config']['User']=='1000:1000' and creation['config']['WorkingDir']=='/candidate'
  mounts=creation['mounts'];assert len(mounts)==2 and all(m['Type']=='bind' and m['RW'] is False for m in mounts)
  paths={m['Destination']:m['Source'] for m in mounts};assert paths['/candidate']==read(MAIN/'trial-download-integrity.json')['rig_root']+'/'+case.name+'/candidate'
  assert paths['/opt/deps'].endswith('/36cd138cbdc332246a2db473301200117f82404a4504c675db95966645348975/deps')
  assert cmd['argv'][cmd['argv'].index('--log-driver')+1]=='none'
  combined=stdout[len(start['nonce'])+1:]+actual['output'].encode()
  feedback={'command':charge['command'],**{k:actual[k] for k in ['exit_code','timed_out','elapsed_s']},'output':combined[:16384].decode(errors='replace'),'output_limited':actual.get('limited',False) or len(combined)>16384}
  commands.append({'number':charge['number'],'feedback':feedback,'stdout_bytes':len(stdout),'elapsed_s':actual['elapsed_s']})
 assert {r['name'] for r in result['cleanup']}=={c['name'] for c in ledger['commands']}
 assert all(c['confirmed_absent'] is True for c in result['cleanup'])
 usages=[];latencies=[];finish=[];max_req=max_resp=0;cursor=0;expected_messages=None
 for charge in ledger['requests']:
  d=case/'requests'/f"{charge['number']:02d}";request=read(d/'request.json');response=read(d/'response.json');wire=read(d/'transport.json')
  assert charge['status']=='returned' and charge['role']=='reviewer'
  assert sha((d/'request.json').read_bytes())==charge['request_sha256'] and sha((d/'response.json').read_bytes())==charge['response_sha256']
  assert read(d/'request.body')==request and read(d/'response.body')==response
  assert wire=={'http_status':200,'complete':True,'bytes_captured':(d/'response.body').stat().st_size}
  assert (d/'request.body').stat().st_size<=4*1024*1024 and (d/'response.body').stat().st_size<=1024*1024
  max_req=max(max_req,(d/'request.body').stat().st_size);max_resp=max(max_resp,(d/'response.body').stat().st_size)
  assert all(enc(request[k])==enc(v) for k,v in profile.items()) and request['tools']==expected_tools and request['tool_choice']=='auto'
  assert request['messages'][0]=={'role':'system','content':expected_system}
  if expected_messages is None:
   assert len(request['messages'])==2 and request['messages'][1]['role']=='user'
   payload=json.loads(request['messages'][1]['content']);assert set(payload)=={'objective','files'}
   assert sha(payload['objective'].encode())==inp['objective_sha256']
   assert {n:sha(text.encode()) for n,text in payload['files'].items()}==expected
  else:assert request['messages']==expected_messages
  assert charge['usage']==response['usage'];usages.append(response['usage']);latencies.append(charge['elapsed_s'])
  choice=response['choices'][0];message=choice['message'];finish.append(choice['finish_reason'])
  expected_messages=request['messages']+[message]
  if choice['finish_reason'] in ['tool_calls','stop'] and message.get('tool_calls'):
   for call in message['tool_calls']:
    assert call['function']['name']=='run' and json.loads(call['function']['arguments'])=={'command':commands[cursor]['feedback']['command']}
    expected_messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(commands[cursor]['feedback'])});cursor+=1
 assert cursor==len(commands)
 terminal=read(case/'requests'/f"{len(ledger['requests']):02d}"/'response.json')['choices'][0]
 if index in (0,2):
  try:json.loads(terminal['message']['content'])
  except json.JSONDecodeError:pass
  else:raise AssertionError('Expected terminal JSON rejection')
  assert result['child']['error_type']=='JSONDecodeError' and not (case/'verdict.json').exists()
 elif index==1:
  assert terminal['finish_reason']=='length' and len(terminal['message']['tool_calls'])==2
  assert result['child']['error']=='Malformed tool completion' and not (case/'verdict.json').exists()
 else:
  assert json.loads(terminal['message']['content'])==result['child']['verdict']==read(case/'verdict.json')
  assert result['child']['attested_commands']==len(commands)==9 and result['child']['verdict']['decision']=='repair'
  assert result['child']['candidate_sha256']==sha(enc(inp['facts']))
 usage={k:countsum(usages,k) for k in ['prompt_tokens','completion_tokens','total_tokens']}
 cache=[u.get('prompt_tokens_details',{}).get('cached_tokens') for u in usages];usage['cached_prompt_tokens']=sum(cache) if all(type(v) is int for v in cache) else None
 usage['missing_usage_records']=sum(any(type(u.get(k)) is not int for k in ['prompt_tokens','completion_tokens','total_tokens']) for u in usages)
 row={'case':case.name,'status':result['status'],'terminal_error':result['child'].get('error_type'),'terminal_finish_reason':terminal['finish_reason'],'requests':len(usages),'commands':len(commands),'usage':usage,'request_elapsed_s_sum':sum(latencies),'request_latency_s':{'min':min(latencies),'median':statistics.median(latencies),'max':max(latencies)},'work_elapsed_s':result['work_elapsed_s'],'cleanup_elapsed_s':result['cleanup_elapsed_s'],'command_elapsed_s_sum':sum(c['elapsed_s'] for c in commands),'command_exit_codes':dict(collections.Counter(str(c['exit_code']) for c in ledger['commands'])),'finish_reasons':dict(collections.Counter(finish)),'max_raw_request_bytes':max_req,'max_raw_response_bytes':max_resp,'idle_pair_gaps_s':gaps,'copied_modes_match_recorded':copied_modes_match,'source_file_count':len(expected),'candidate_facts_sha256':sha(enc(inp['facts'])),'cleanup_and_idle_confirmed':True,'remaining_credits':8-len(usages),'unexecuted_terminal_tool_calls':2 if index==1 else 0}
 cases.append(row);all_usage.extend(usages);all_request_times.extend(latencies);all_commands.extend(commands)
assert facts(ROOT)==before
summary={'outcome':'PASS accounting/lifetime audit; discriminator quality gate is separate and failed overall','prototype_commit':candidate['prototype_commit'],'admission_sha256':sha((MAIN/'trial-1-admission.json').read_bytes()),'download_manifest_sha256':sha((MAIN/'trial-artifact-hashes.json').read_bytes()),'manifest_entries_verified':325,'all_artifacts_unchanged':True,'cases':cases,'totals':{'requests':len(all_usage),'commands':len(all_commands),'completed_reviews':sum(c['status']=='accepted' for c in cases),'incomplete_reviews':sum(c['status']=='incomplete' for c in cases),'usage':{k:sum(c['usage'][k] for c in cases) for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens','missing_usage_records']},'work_elapsed_s_sum':sum(c['work_elapsed_s'] for c in cases),'cleanup_elapsed_s_sum':sum(c['cleanup_elapsed_s'] for c in cases),'request_elapsed_s_sum':sum(all_request_times),'command_elapsed_s_sum':sum(c['elapsed_s'] for c in all_commands)},'serving_identity':identity,'observed_scope':'Persisted receipts and frozen controller/transport logic; no live query, candidate execution or independent packet capture. Local copied artifacts cannot prove absence of unrelated serving clients. No unrecorded retries in this admitted controller trajectory.'}
(MAIN/'trial-accounting.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary['totals'],indent=2))
