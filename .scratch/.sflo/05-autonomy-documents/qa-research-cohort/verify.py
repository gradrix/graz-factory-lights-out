import pathlib,json,hashlib
r=pathlib.Path('.gflo/document-research-cohort');contracts=pathlib.Path('.scratch/.sflo/05-autonomy-documents/research-cohort');out=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((contracts/'manifest.json').read_text())
for name,h in m['contracts'].items():assert sha((contracts/name).read_bytes())==h
rows=[]
for group in ['json','csv','asyncio_groups','asyncio_timeouts']:
 p=r/group;receipt=json.loads((p/'receipt.json').read_text());assert receipt['candidate_manifest']==m['candidate_manifest_sha256'];assert receipt['contract_sha256']==m['contracts'][group+'.json']
 if not receipt['questions']:rows.append({'group':group,'questions_attempted':0,'recorded_failure':receipt.get('failure')});continue
 e=json.loads((p/'evidence.json').read_text());store=p/'store';assert sha((store/e['id']/'receipt.json').read_bytes())==e['id'];assert sha((store/e['id']/'body').read_bytes())==e['receipt']['body_sha256'];assert sha((store/e['id']/'text').read_bytes())==e['receipt']['text_sha256']
 for row in receipt['questions']:
  raw=json.loads((p/(row['name']+'-response.json')).read_text());answer=json.loads(raw['choices'][0]['message']['content']);checks=[]
  for i,claim in enumerate(answer['claims'],1):
   for cite in claim['citations']:
    span=e['spans'][cite['span']-1];matches=cite['evidence_id']==e['id'] and cite['excerpt'] in span;checks.append({'claim':i,'span':cite['span'],'exact':matches})
  if row.get('answer_id'):assert all(c['exact'] for c in checks);assert sha((store/row['answer_id']/'receipt.json').read_bytes())==row['answer_id']
  if row['name']=='row_shape':
   bad=[c for c in checks if not c['exact']];assert bad==[{'claim':2,'span':44,'exact':False}];assert answer['claims'][1]['citations'][0]['excerpt'].replace("isn't","isn’t") in e['spans'][43]
  rows.append({'group':group,'name':row['name'],'saved':bool(row.get('answer_id')),'elapsed_s':row['elapsed_s'],'citations':checks})
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS frozen identities and precise citation discrepancy verified')
