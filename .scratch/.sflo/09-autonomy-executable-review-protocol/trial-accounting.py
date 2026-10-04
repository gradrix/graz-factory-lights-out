#!/usr/bin/env python3
"""Read-only artifact audit: never imports/executes candidates or contacts services."""
import ast, collections, datetime, hashlib, json, re, statistics
from pathlib import Path

MAIN=Path(__file__).resolve().parent
REPO=MAIN.parents[2]
ROOT=REPO/'.gflo/executable-review-protocol-trial-1'
PROTO=Path('/home/gradrix/repos/gflo-review-protocol-prototype')
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
assert all(before[n]==v for n,v in manifest.items())
assert set(before)==set(manifest)|{'artifact-hashes.json'}
assert read(ROOT/'artifact-hashes.json')==manifest
assert read(MAIN/'trial-download-integrity.json')['manifest_sha256']==sha((MAIN/'trial-artifact-hashes.json').read_bytes())
admission=read(MAIN/'trial-1-admission.json');candidate=read(MAIN/'builder-candidate.json')
assert sha((MAIN/'trial-1-admission.json').read_bytes())==read(MAIN/'trial-1-process.json')['admission_sha256']
assert admission['prototype_commit']==candidate['candidate_commit']=='847f90e9d4fe515e6c6eada9eb200008b6441fd2'
assert all(sha((PROTO/n).read_bytes())==v for n,v in {**candidate['source_sha256'],**read(MAIN/'carry-forward.json')['reused_source_sha256']}.items())
assert all(sha((MAIN/n).read_bytes())==v for n,v in admission['gates_sha256'].items())
fixture=read(PROTO/'evaluations/executable-review/manifest.json');profile=read(ROOT/'experiment.json')['profile']
assert profile=={'model':'flash-next-coder','temperature':0,'max_tokens':4096,'reasoning_effort':'medium','thinking_budget_tokens':1024,'chat_template_kwargs':{'enable_thinking':True}}
review_system=ast.literal_eval(assignment(PROTO/'gflo/review.py','SYSTEM'))
system_ast=assignment(PROTO/'ops/executable_review_prototype.py','SYSTEM')
expected_system=review_system.replace(*[ast.literal_eval(v) for v in system_ast.left.args])+ast.literal_eval(system_ast.right)
for node in ast.parse((PROTO/'ops/executable_review_prototype.py').read_text()).body:
 if isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='SYSTEM':expected_system+=ast.literal_eval(node.value)
expected_tools=ast.literal_eval(assignment(PROTO/'ops/executable_review_prototype.py','TOOLS'))
identity=read(MAIN/'pre-admission-idle.json')['identity']
results=read(ROOT/'results.json');assert results==read(MAIN/'trial-results.json')
assert [r['case'] for r in results]==admission['order']==['case-01','case-02','case-03','case-04']
cases=[];all_usage=[];all_request_times=[];names=set();all_commands=[]
FINAL_FEEDBACK='Controller phase transition: execution is closed. Return only the exact grounded JSON review object from the original objective, source and actual recorded evidence. No tools are available. Do not claim checks that did not run or exhaustive coverage.'
for index,result in enumerate(results):
 case=ROOT/result['case'];ledger=read(case/'ledger.json');inp=read(case/'input.json');events=[json.loads(line) for line in (case/'progress.jsonl').read_text().splitlines()]
 assert result==read(case/'result.json') and result['child']==read(case/'child-result.json')
 assert ledger['request_limit']==8 and ledger['command_limit']==12 and len(ledger['requests'])<=8 and len(ledger['commands'])<=12
 assert ledger['exploration_deadline']==ledger['deadline']-120
 assert all(type(x.get('phase')) is str for x in ledger['requests'])
 phases=[x['phase'] for x in ledger['requests']]
 assert phases.count('explore')<=7 and phases.count('final')<=1
 assert phases==['explore']*phases.count('explore')+['final']*phases.count('final')
 assert ledger['final_reserved'] is bool(phases.count('final'))
 transitions=[e for e in events if e['event']=='phase_transition'];recoveries=[e for e in events if e['event']=='length_recovery']
 assert len(transitions)<=1 and len(recoveries)<=1 and ledger['recovery_used'] is bool(recoveries)
 assert all(x['phase']=='explore' for x in ledger['commands'])
 dispatched_by_request=collections.defaultdict(list);current_request=0
 for event in events:
  if event['event']=='requests_reserved':current_request=event['number']
  elif event['event']=='commands_reserved':dispatched_by_request[current_request].append(event['number'])
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
  assert charge['exit_code']==actual['exit_code'] and charge['timed_out']==actual['timed_out']
  assert creation['name']==cleanup['name']==charge['name'] and cleanup['confirmed_absent'] is True
  assert creation['image']=='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
  host=creation['host'];assert host['Runtime']=='runc' and host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True
  assert host['CapDrop']==['ALL'] and 'no-new-privileges' in host['SecurityOpt'] and not host['Devices'] and not host['DeviceRequests']
  for k,v in {'Memory':1073741824,'MemorySwap':1073741824,'NanoCpus':2000000000,'PidsLimit':128,'ShmSize':16777216,'Tmpfs':{'/tmp':'rw,nosuid,nodev,size=128m'}}.items():assert host[k]==v
  assert creation['config']['User']=='1000:1000' and creation['config']['WorkingDir']=='/candidate'
  mounts=creation['mounts'];assert len(mounts)==2 and all(m['Type']=='bind' and m['RW'] is False for m in mounts)
  paths={m['Destination']:m['Source'] for m in mounts};assert paths['/candidate']==read(MAIN/'trial-1-process.json')['output']+'/'+case.name+'/candidate'
  assert paths['/opt/deps'].endswith('/36cd138cbdc332246a2db473301200117f82404a4504c675db95966645348975/deps')
  assert cmd['argv'][cmd['argv'].index('--log-driver')+1]=='none'
  combined=stdout[len(start['nonce'])+1:]+actual['output'].encode()
  feedback={'command':charge['command'],**{k:actual[k] for k in ['exit_code','timed_out','elapsed_s']},'output':combined[:16384].decode(errors='replace'),'output_limited':actual.get('limited',False) or len(combined)>16384}
  commands.append({'number':charge['number'],'feedback':feedback,'stdout_bytes':len(stdout),'elapsed_s':actual['elapsed_s']})
 assert {r['name'] for r in result['cleanup']}=={c['name'] for c in ledger['commands']}
 assert all(c['confirmed_absent'] is True for c in result['cleanup'])
 usages=[];latencies=[];finish=[];max_req=max_resp=0;cursor=0;expected_messages=None;pending_recovery=False;projection_records=[]
 for charge in ledger['requests']:
  d=case/'requests'/f"{charge['number']:02d}";request=read(d/'request.json');response=read(d/'response.json');wire=read(d/'transport.json')
  assert charge['status']=='returned' and charge['role']=='reviewer'
  assert sha((d/'request.json').read_bytes())==charge['request_sha256'] and sha((d/'response.json').read_bytes())==charge['response_sha256']
  assert read(d/'request.body')==request and read(d/'response.body')==response
  assert wire=={'http_status':200,'complete':True,'bytes_captured':(d/'response.body').stat().st_size}
  assert (d/'request.body').stat().st_size<=4*1024*1024 and (d/'response.body').stat().st_size<=1024*1024
  max_req=max(max_req,(d/'request.body').stat().st_size);max_resp=max(max_resp,(d/'response.body').stat().st_size)
  assert all(enc(request[k])==enc(v) for k,v in profile.items())
  if charge['phase']=='explore':assert request['tools']==expected_tools and request['tool_choice']=='auto' and 'response_format' not in request
  else:assert 'tools' not in request and 'tool_choice' not in request and request['response_format']=={'type':'json_object'}
  assert request['messages'][0]=={'role':'system','content':expected_system}
  if expected_messages is None:
   assert len(request['messages'])==2 and request['messages'][1]['role']=='user'
   payload=json.loads(request['messages'][1]['content']);assert set(payload)=={'objective','files'}
   assert sha(payload['objective'].encode())==inp['objective_sha256']
   assert {n:sha(text.encode()) for n,text in payload['files'].items()}==expected
  else:
   if pending_recovery and charge['phase']=='explore':
    # Recovery feedback has a measured remaining-seconds field; validate its exact
    # fixed text/counters and numeric bound without inventing its sampling time.
    assert charge['phase']=='explore' and len(request['messages'])==len(expected_messages)+1
    assert request['messages'][:-1]==expected_messages and request['messages'][-1]['role']=='user'
    text=request['messages'][-1]['content']
    prefix=('Controller protocol feedback: the previous response was truncated; no commands from it ran. '
            'Return one compact valid run call. Generate repetitive test inputs programmatically. '
            f'Remaining exploration requests: {7-(charge["number"]-1)}; commands: {12-cursor}; exploration seconds: ')
    assert text.startswith(prefix) and re.fullmatch(r'[0-9]+\.',text[len(prefix):])
    assert 0<=int(text[len(prefix):-1])<=180
   elif charge['phase']=='final':assert request['messages']==expected_messages+[{'role':'user','content':FINAL_FEEDBACK}]
   else:assert request['messages']==expected_messages
  assert response['usage']['prompt_tokens']+response['usage']['completion_tokens']==response['usage']['total_tokens']
  assert 0<=response['usage']['prompt_tokens_details']['cached_tokens']<=response['usage']['prompt_tokens']
  assert charge['usage']==response['usage'];usages.append(response['usage']);latencies.append(charge['elapsed_s'])
  choice=response['choices'][0];message=choice['message'];finish.append(choice['finish_reason'])
  expected_messages=list(request['messages']);pending_recovery=False
  actual_numbers=dispatched_by_request[charge['number']]
  if charge['phase']=='final':
   assert not actual_numbers
  elif choice['finish_reason']=='length':
   assert not actual_numbers
   pending_recovery=True
   projection_records.append({'request':charge['number'],'kind':'length-whole-batch-refused','executed':0})
  elif message.get('tool_calls'):
   calls=message['tool_calls'];assert isinstance(calls,list)
   executed=[];feedback=[]
   for call,number in zip(calls,actual_numbers):
    assert number==cursor+1
    assert call['function']['name']=='run' and json.loads(call['function']['arguments'])=={'command':commands[cursor]['feedback']['command']}
    executed.append(call);feedback.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(commands[cursor]['feedback'])});cursor+=1
   assert len(actual_numbers)<=len(calls)
   if executed:expected_messages.append({**message,'tool_calls':executed});expected_messages.extend(feedback)
   if len(executed)<len(calls):
    skipped=[call['id'] for call in calls[len(executed):]]
    expected_messages.append({'role':'user','content':'Controller phase boundary: remaining proposed calls '+json.dumps(skipped)+' were not executed. Use only actual recorded command results.'})
    assert any(e['event']=='exploration_calls_skipped' and e['ids']==skipped for e in events)
   projection_records.append({'request':charge['number'],'kind':'tool-history-projection','proposed':len(calls),'executed':len(executed)})
  else:
   assert not actual_numbers
   expected_messages.append(message)
 assert cursor==len(commands)
 terminal=read(case/'requests'/f"{len(ledger['requests']):02d}"/'response.json')['choices'][0]
 terminal_final=ledger['requests'][-1]['phase']=='final'
 if result['child']['status']=='accepted':
  assert terminal_final and terminal['finish_reason']=='stop'
  final_message=terminal['message'];assert final_message['role']=='assistant' and final_message.get('tool_calls') in (None,[]) and final_message.get('function_call') is None
  assert json.loads(final_message['content'])==result['child']['verdict']==read(case/'verdict.json')
  assert result['child']['attested_commands']==len(commands)>0
  assert result['child']['candidate_sha256']==sha(enc(inp['facts']))
 else:assert not (case/'verdict.json').exists()
 if terminal_final:assert len(transitions)==1 and ledger['phase']=='final'
 usage={k:countsum(usages,k) for k in ['prompt_tokens','completion_tokens','total_tokens']}
 cache=[u.get('prompt_tokens_details',{}).get('cached_tokens') for u in usages];usage['cached_prompt_tokens']=sum(cache) if all(type(v) is int for v in cache) else None
 usage['missing_usage_records']=sum(any(type(u.get(k)) is not int for k in ['prompt_tokens','completion_tokens','total_tokens']) for u in usages)
 row={'case':case.name,'status':result['status'],'terminal_error':result['child'].get('error_type'),'terminal_finish_reason':terminal['finish_reason'],'requests':len(usages),'commands':len(commands),'usage':usage,'request_elapsed_s_sum':sum(latencies),'request_latency_s':{'min':min(latencies),'median':statistics.median(latencies),'max':max(latencies)},'work_elapsed_s':result['work_elapsed_s'],'cleanup_elapsed_s':result['cleanup_elapsed_s'],'command_elapsed_s_sum':sum(c['elapsed_s'] for c in commands),'exploration_request_elapsed_s_sum':sum(x['elapsed_s'] for x in ledger['requests'] if x['phase']=='explore'),'final_request_elapsed_s':next((x['elapsed_s'] for x in ledger['requests'] if x['phase']=='final'),None),'command_timeouts':sum(x['timed_out'] for x in ledger['commands']),'command_output_limits':sum(read(case/'commands'/f"{x['number']:02d}"/'result.json')['limited'] for x in ledger['commands']),'command_exit_codes':dict(collections.Counter(str(c['exit_code']) for c in ledger['commands'])),'finish_reasons':dict(collections.Counter(finish)),'max_raw_request_bytes':max_req,'max_raw_response_bytes':max_resp,'idle_pair_gaps_s':gaps,'copied_modes_match_recorded':copied_modes_match,'source_file_count':len(expected),'candidate_facts_sha256':sha(enc(inp['facts'])),'cleanup_and_idle_confirmed':True,'remaining_credits':8-len(usages),'exploration_requests':phases.count('explore'),'final_requests':phases.count('final'),'recovery_count':len(recoveries),'transition_reason':ledger.get('transition_reason'),'history_projection':projection_records,'verdict_decision':result['child'].get('verdict',{}).get('decision'),'unexecuted_terminal_tool_calls':len(terminal['message'].get('tool_calls') or [])-len(dispatched_by_request[len(ledger['requests'])])}
 cases.append(row);all_usage.extend(usages);all_request_times.extend(latencies);all_commands.extend(commands)
assert all(c['requests']==c['exploration_requests']+c['final_requests'] for c in cases)
assert facts(ROOT)==before
summary={'outcome':'PASS accounting/lifetime audit; classification quality remains separate','prototype_commit':candidate['candidate_commit'],'admission_sha256':sha((MAIN/'trial-1-admission.json').read_bytes()),'download_manifest_sha256':sha((MAIN/'trial-artifact-hashes.json').read_bytes()),'manifest_entries_verified':len(manifest),'all_artifacts_unchanged':True,'cases':cases,'totals':{'requests':len(all_usage),'commands':len(all_commands),'exploration_requests':sum(c['exploration_requests'] for c in cases),'final_requests':sum(c['final_requests'] for c in cases),'recoveries':sum(c['recovery_count'] for c in cases),'completed_reviews':sum(c['status']=='accepted' for c in cases),'incomplete_reviews':sum(c['status']=='incomplete' for c in cases),'usage':{k:sum(c['usage'][k] for c in cases) for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens','missing_usage_records']},'work_elapsed_s_sum':sum(c['work_elapsed_s'] for c in cases),'cleanup_elapsed_s_sum':sum(c['cleanup_elapsed_s'] for c in cases),'request_elapsed_s_sum':sum(all_request_times),'command_elapsed_s_sum':sum(c['elapsed_s'] for c in all_commands)},'serving_identity':identity,'observed_scope':'Persisted receipts and frozen controller/transport logic; no live query, candidate execution or independent packet capture. Local copied artifacts cannot prove absence of unrelated serving clients. No unrecorded retries in this admitted controller trajectory.'}
(MAIN/'trial-accounting.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary['totals'],indent=2))
