"""Offline provenance/discrimination audit; no client/model calls."""
import ast,copy,hashlib,json,sys
from pathlib import Path
base=Path('.gflo/document-citation-prototype');public=Path('.scratch/autonomy/document-citation-prototype');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();contract=json.loads((public/'contract.json').read_text());assert sha(public/'contract.json')=='03f51ebe72780e13df4435f50f5306ea3736d5e797f4c5ca4a1ff7b66206adf8'
for n,h in contract['input_hashes'].items():assert sha(base/n)==h,n
sys.path.insert(0,str((base/'source').resolve()));from gflo.documents import validate_answer,decode
node=next(x for x in ast.parse((base/'prototype.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='refs');scope={'copy':copy,'validate_answer':validate_answer};exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen-refs>','exec'),scope);refs=scope['refs']
rows=json.loads((base/'results/results.json').read_text());assert len(rows)==8;audits=[]
for row in rows:
 case=next(x for x in contract['cases'] if x['name']==row['case']);evidence=json.loads((base/f"inputs/{case['source']}.json").read_text());attempts=[]
 for attempt in row['attempts']:
  path=base/f"results/{row['case']}/{row['method']}/{attempt['attempt']}";request=json.loads((path/'request.json').read_text());assert request['model']=='flash-next-coder' and request['temperature']==0 and request['max_tokens']==2048 and request['reasoning_effort']=='medium' and request['thinking_budget_tokens']==512
  raw=json.loads((path/'response.raw.json').read_text());assert raw==json.loads((path/'response.json').read_text());content=raw['choices'][0]['message']['content'];assert content==(path/'content.txt').read_text();value=decode(content)
  error=None
  try:checked=(refs if row['method']=='references' else validate_answer)(value,evidence)
  except ValueError as e:error=str(e)
  assert error==attempt.get('validation_error');attempts.append({'number':attempt['attempt'],'error':error,'raw_sha256':sha(path/'response.raw.json')})
  if not error:assert checked==row['answer']
 audits.append({'case':row['case'],'method':row['method'],'attempts':attempts,'elapsed_s':row['elapsed_s'],'excerpt_bytes':sum(len(c['excerpt'].encode()) for claim in row['answer']['claims'] for c in claim['citations'])})
e=json.loads((base/'inputs/csv.json').read_text());synthetic=copy.deepcopy(e);synthetic['spans'][0]='a'*4097
value={'status':'supported','claims':[{'text':'Synthetic limit control','citations':[{'evidence_id':e['id'],'span':1}]}],'reason':''}
try:refs(value,synthetic)
except ValueError as error:long_error=str(error)
else:raise AssertionError('4097-byte whole span accepted')
short=copy.deepcopy(value);short['claims'][0]['citations'][0]['excerpt']='a';validate_answer(short,synthetic)
wrong=copy.deepcopy(rows[1]['answer']);wrong['claims'][0]['text']='Python 3.16 changes restval on 2030-01-01.';validate_answer(wrong,e)
result={'all_bound_input_hashes_match':True,'rows':audits,'source_max_span_bytes':{n:max(len(x.encode())for x in json.loads((base/f'inputs/{n}.json').read_text())['spans'])for n in ['csv','json']},'long_whole_span_error':long_error,'short_exact_excerpt_in_long_span_valid':True,'deliberately_false_claim_with_valid_citation_structurally_accepted':True}
(public/'qa/verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
