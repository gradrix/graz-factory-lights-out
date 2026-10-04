"""Read persisted evidence only; no endpoint, Docker, or model calls."""
from pathlib import Path
import json,hashlib,subprocess
r=Path(__file__).resolve().parent;e=r/'rig-cancellation-1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
a=load(r/'cancellation-admission.json');events=load(e/'events.json');result=load(e/'result.json');expected=load(r/'serving-lifecycle/expected-identity.json');request=load(e/'request.json');debit=load(e/'debit.json');started=load(e/'client-started.json')
assert sha(r/'cancellation-admission.json')=='69d38f8aa5bd597fbefd239707fdbe3a49ccee01097134127aa5daf33ce7c689'
assert a==load(e/'admission.json') # Driver save reserializes and omits trailing newline.
assert sha(r/'serving-lifecycle/expected-identity.json')==a['identity_sha256']
assert hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()==a['request_sha256']
for kind,binding in a['evidence'].items():assert sha(r/Path(binding['path']).name)==binding['sha256'],kind
for path,wanted in a['prototype_files'].items():
 body=subprocess.check_output(['git','show',a['prototype_commit']+':'+path],cwd='/home/gradrix/repos/gflo-planning-prototype');assert hashlib.sha256(body).hexdigest()==wanted,path
observations=[v for v in events if 'observation' in v]
assert all(v['observation']['identity']==expected for v in observations)
assert [v['elapsed_s'] for v in events]==sorted(v['elapsed_s'] for v in events)
pre=[v for v in events if v['kind']=='preflight'];idle=[v for v in events if v['kind']=='cleanup_observation' and v['observation']['state']=='idle'];stop=next(v for v in events if v['kind']=='stop_transition');cleanup=next(v for v in events if v['kind']=='client_cleanup');launch=next(v for v in events if v['kind']=='client_launched')
assert len(pre)==2 and all(v['observation']['state']=='idle' for v in pre) and pre[1]['elapsed_s']-pre[0]['elapsed_s']>=1
assert any(v['kind']=='active_observation' and v['observation']['state']=='busy' and v['observation']['slots'][0]['is_processing'] is True for v in events)
assert stop['alive'] is True and stop['completed'] is False and stop['observed_busy'] is True
assert cleanup['actions']==['SIGTERM'] and cleanup['returncode']==-15 and cleanup['group_absent'] is True
assert len(idle)==2 and idle[1]['elapsed_s']-idle[0]['elapsed_s']>=1
assert debit['count']==debit['limit']==result['charged_requests']==1 and debit['monotonic']<started['monotonic'] and started['pid']==launch['pid']
assert not (e/'response.json').exists() and not (e/'client-complete.json').exists()
assert result['outcome']=='passed' and result['cleanup_s']<150 and stop['elapsed_s']<60
facts={'outcome':'PASS_readback','admission_sha256':sha(r/'cancellation-admission.json'),'admission_copy_sha256':sha(e/'admission.json'),'admission_json_identical':True,'commit':a['prototype_commit'],'verified_code_files':len(a['prototype_files']),'observations':len(observations),'identities_equal':True,'preflight_idle_gap_s':pre[1]['elapsed_s']-pre[0]['elapsed_s'],'final_idle_gap_s':idle[1]['elapsed_s']-idle[0]['elapsed_s'],'first_idle_after_stop_s':idle[0]['elapsed_s']-stop['elapsed_s'],'stop_s':stop['elapsed_s'],'total_s':result['elapsed_s'],'cleanup_s':result['cleanup_s'],'files':{p.name:sha(p) for p in sorted(e.iterdir()) if p.is_file()}}
(r/'qa-rig-cancellation-readback.json').write_text(json.dumps(facts,indent=2)+'\n');print(json.dumps({k:v for k,v in facts.items() if k!='files'},indent=2))
