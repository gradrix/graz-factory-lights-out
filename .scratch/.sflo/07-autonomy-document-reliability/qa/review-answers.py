"""Offline recorded-response provenance audit; semantic judgments remain manual."""
import argparse,hashlib,json,pathlib,sys
p=argparse.ArgumentParser();p.add_argument('full',type=pathlib.Path);a=p.parse_args();base=pathlib.Path('.scratch/.sflo/07-autonomy-document-reliability');qual=pathlib.Path('.scratch/autonomy/document-repair-qualification');oracle={r['name']:r for r in json.loads((qual/'oracle.json').read_text())};summary=json.loads((a.full/'answers/summary.json').read_text());assert summary['status']=='complete_pending_independent_semantic_review' and len(summary['rows'])==10;rows=[]
for row in summary['rows']:
 n=row['name'];case=oracle[n];e=json.loads((a.full/(case['source']+'-evidence.json')).read_text());rec=json.loads((a.full/'answers'/n/'receipt.json').read_text());saved=a.full/'store'/row['id'];raw=(saved/'receipt.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==row['id'] and json.loads(raw)==rec['receipt'];rec=rec['receipt'];assert rec['kind']in ['answer','answer_failure'];answer=json.loads((a.full/'answers'/n/'answer.json').read_text())['answer'] if rec['kind']=='answer' else None;assert answer is None or (rec['answer']==answer and answer['status']==case['expected_status']);assert row['public_answer_invocations']==1 and len(rec['attempts'])<=2
 attempts=[]
 for attempt in rec['attempts']:
  p=saved/f"response-{attempt['number']}.json";raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==attempt['response_sha256'] and len(raw)==attempt['response_size'];response=json.loads(raw);content=response['choices'][0]['message']['content'];
  try:value=json.loads(content)
  except ValueError:
   assert attempt['validation']=='invalid';attempts.append({'number':attempt['number'],'validation':'invalid','content':content,'error':attempt['error']});continue
  claims=[]
  for claim in value['claims']:
   citations=[]
   for cite in claim['citations']:
    assert cite['evidence_id']==e['id'] and type(cite['span'])is int and 1<=cite['span']<=len(e['spans']);citations.append({'span':cite['span'],'matches':cite['excerpt']in e['spans'][cite['span']-1],'excerpt':cite['excerpt']})
   claims.append({'text':claim['text'],'citations':citations})
  attempts.append({'number':attempt['number'],'validation':attempt['validation'],'error':attempt['error'],'status':value['status'],'reason':value['reason'],'claims':claims,'completion_tokens':response.get('usage',{}).get('completion_tokens'),'finish_reason':response['choices'][0].get('finish_reason')})
 if answer is not None:assert all(c['matches']for claim in attempts[-1]['claims']for c in claim['citations'])
 rows.append({'name':n,'exposure':case['exposure'],'status':answer['status'] if answer else 'answer_failure','elapsed_s':row['elapsed_s'],'attempts':attempts})
(base/'qa/answer-review-evidence.json').write_text(json.dumps(rows,indent=2)+'\n');print('Recorded10outcomes/receipt-responsehashes/publishedcitations; failures retained; manual semantic review required')
