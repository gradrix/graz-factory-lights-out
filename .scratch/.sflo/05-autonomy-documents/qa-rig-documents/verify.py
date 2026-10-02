import pathlib,json,hashlib,sys,subprocess
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('20493612b62de19a5e4dbb713803abd8a9667b0b')
from gflo.documents import DocumentStore,encoded,digest,answer_request,validate_answer
r=pathlib.Path('.gflo/document-rig-trial-1');out=pathlib.Path(__file__).resolve().parent;trial=json.loads((r/'receipt.json').read_text());m=pathlib.Path('.scratch/.sflo/05-autonomy-documents/builder-candidate-v2.json');assert digest(m.read_bytes())==trial['candidate_manifest']
for name,h in json.loads(m.read_text())['files'].items():assert digest(subprocess.check_output(['git','show','2049361:'+name]))==h
contract=pathlib.Path('.scratch/.sflo/05-autonomy-documents/rig-trial-contract.json');assert digest(contract.read_bytes())==trial['contract_sha256'];contract=json.loads(contract.read_text());store=DocumentStore(r/'store');e=store.resolve(trial['evidence_id']);assert e['receipt']==json.loads((r/'evidence.json').read_text())['receipt']
for name,h in trial['offline_replay']['record_hashes'].items():assert digest((r/'store'/name).read_bytes())==h
replays=json.loads((r/'offline-replay.json').read_text());assert replays['python']=='3.12.13';checks=[]
for q,row,replayed in zip(contract['questions'],trial['questions'],replays['answers']):
 answer=json.loads((r/(q['name']+'-answer.json')).read_text());saved=store.resolve(row['answer_id'])['receipt'];raw=json.loads((r/(q['name']+'-response.json')).read_text());req=json.loads((r/(q['name']+'-request.json')).read_text())
 assert raw==saved['response'] and digest(encoded(raw))==saved['response_sha256'];assert digest(q['question'].encode())==saved['question_sha256'];assert saved['question']==q['question']
 reconstructed=answer_request(e,'flash-next-coder',q['question']);assert digest(encoded(reconstructed))==req['request_sha256']==saved['request_sha256'];assert req['timeout_s']==120 and req['max_response_bytes']==65536 and req['max_tokens']==2048 and req['thinking_budget_tokens']==512 and req['reasoning_effort']=='medium' and not req['tools_present']
 assert validate_answer(answer['answer'],e)==saved['answer'];assert raw['choices'][0]['finish_reason']=='stop';assert raw['usage']['completion_tokens']<=2048
 assert {k:v for k,v in answer.items() if k!='age_seconds'}=={k:v for k,v in replayed.items() if k!='age_seconds'};assert row['attempts']==1
 expected='insufficient_evidence' if q['expected_status']=='insufficient' else q['expected_status'];assert answer['answer']['status']==expected
 checks.append({'name':q['name'],'answer_id':answer['id'],'citation_count':sum(len(c['citations']) for c in answer['answer']['claims']),'elapsed_s':row['elapsed_s'],'usage':raw['usage'],'request_response_hashes':True,'replay_equal_except_age':True})
facts=json.loads((r/'replay-executor.json').read_text());assert facts['host']['NetworkMode']=='none' and facts['host']['Runtime']=='runc';assert len(facts['mounts'])==2;assert {(x['Destination'],x['RW']) for x in facts['mounts']}=={('/app/gflo',False),('/store',True)};assert not facts['host']['Devices'] and not facts['host']['DeviceRequests'];assert trial['serving_before']==trial['serving_after'];assert trial['serving_before']['context']==98304 and trial['serving_before']['cache_k']==trial['serving_before']['cache_v']=='q4_0'
(out/'results.json').write_text(json.dumps({'candidate':'20493612b62de19a5e4dbb713803abd8a9667b0b','checks':checks,'record_hashes':True,'replay_executor_verified':True,'total_elapsed_s':trial['elapsed_s']},indent=2)+'\n');print('PASS identity/request/response/citations/budgets/replay evidence')
