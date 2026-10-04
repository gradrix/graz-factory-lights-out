"""Offline format3 attempt/provenance audit; manual semantic review remains required."""
import argparse,hashlib,json,pathlib,sys
p=argparse.ArgumentParser();p.add_argument('full',type=pathlib.Path);a=p.parse_args();sys.path.insert(0,str(pathlib.Path.cwd()))
from gflo.documents import encoded,repair_request
from gflo.document_references import reference_request,reference_response
base=pathlib.Path('.scratch/.sflo/07-autonomy-document-references');q=pathlib.Path('.scratch/autonomy/document-reference-qualification');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();oracle=json.loads((q/'oracle.json').read_text());cases={x['name']:(group,x) for group,values in oracle.items()for x in values};summary=json.loads((a.full/'answers/summary.json').read_text());assert summary['status']=='complete_pending_independent_semantic_review' and len(summary['rows'])==13
manifest=base/'builder-candidate.json';assert sha(manifest)=='acd723171fe9b3f5ce9b90b2dc8aea29dbb5e57d41854cf322798690556bc698'
for n,h in json.loads(manifest.read_text())['files'].items():assert sha(pathlib.Path(n))==h
rows=[]
for row in summary['rows']:
 name=row['name'];group,case=cases[name];e=json.loads((a.full/(case['source']+'-evidence.json')).read_text());rec=json.loads((a.full/'answers'/name/'receipt.json').read_text())['receipt'];store=a.full/'store'/row['id'];assert sha(store/'receipt.json')==row['id'] and json.loads((store/'receipt.json').read_text())==rec;assert rec['format']==3 and row['public_answer_invocations']==1;request=reference_request(e,'flash-next-coder',case['question']);assert json.loads((a.full/'answers'/name/'initial-request.json').read_text())==request;attempts=[]
 for item in rec['attempts']:
  assert hashlib.sha256(encoded(request)).hexdigest()==item['request_sha256'];raw=(store/f"response-{item['number']}.json").read_bytes();assert hashlib.sha256(raw).hexdigest()==item['response_sha256'] and len(raw)==item['response_size'];response=json.loads(raw);validation,error,canonical=reference_response(response,e);assert validation==item['validation'] and error==item['error'];content=response['choices'][0]['message']['content'];attempts.append({'number':item['number'],'validation':validation,'error':error,'raw_content':content,'canonical':canonical,'completion_tokens':response.get('usage',{}).get('completion_tokens'),'finish_reason':response['choices'][0].get('finish_reason')})
  if validation=='invalid':request=repair_request(request,response,error)
 if rec['kind']=='answer':
  answer=json.loads((a.full/'answers'/name/'answer.json').read_text())['answer'];assert answer==rec['answer']==attempts[-1]['canonical'];assert answer['status']==case['expected_status']
  for claim in answer['claims']:
   for cite in claim['citations']:assert cite['evidence_id']==e['id'] and cite['excerpt']==e['spans'][cite['span']-1]
 else:answer=None
 rows.append({'name':name,'group':group,'status':answer['status'] if answer else 'answer_failure','elapsed_s':row['elapsed_s'],'attempts':attempts})
(base/'qa/answer-review-evidence.json').write_text(json.dumps(rows,indent=2)+'\n');print('Verified13record/request/response/canonical identities; manual semantics separate')
