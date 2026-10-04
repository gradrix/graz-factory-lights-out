"""New response-reader authority and bounded repair controls."""
import copy,json,pathlib,tempfile
from unittest.mock import patch
import fixture
d=fixture.d;rows=[]
for mode in ['tool','function','envelope','transport','invalid-id-repaired']:
 with tempfile.TemporaryDirectory(dir=fixture.PRIVATE) as td:
  store,ev,client,unused=fixture.fixture(pathlib.Path(td));valid={'status':'supported','claims':[{'text':'Claim','spans':[1]}],'reason':''};response=fixture.response(valid)
  if mode=='tool':response['choices'][0]['message']['tool_calls']=[{}]
  if mode=='function':response['choices'][0]['message']['function_call']={}
  if mode=='envelope':response={}
  values=[response];calls=[]
  if mode=='invalid-id-repaired':bad=copy.deepcopy(valid);bad['claims'][0]['spans']=[0];values=[fixture.response(bad),response]
  def infer(client,request,*a,**kw):
   calls.append(copy.deepcopy(request))
   if mode=='transport':raise ValueError('controlled transport failure')
   return values[len(calls)-1]
  saved=None;error=None
  with patch.object(d,'bounded_answer',infer):
   try:saved=store.answer(ev['id'],client)
   except d.AnswerFailure as e:error=e
  if mode=='invalid-id-repaired':
   assert saved and len(calls)==2
   assert calls[1]['messages'][:2]==calls[0]['messages']
   assert {k:v for k,v in calls[0].items() if k!='messages'}=={k:v for k,v in calls[1].items() if k!='messages'}
   assert calls[1]['messages'][-1]['role']=='user' and 'untrusted output' in calls[1]['messages'][-1]['content']
   receipt=store.resolve(saved['id'])['receipt'];assert [a['validation'] for a in receipt['attempts']]==['invalid','valid']
  else:
   assert error and len(calls)==1;receipt=store.resolve(error.identifier)['receipt'];assert receipt['kind']=='answer_failure'
  assert all('tools' not in x and 'functions' not in x for x in calls)
  rows.append({'case':mode,'calls':len(calls),'kind':receipt['kind'],'validations':[a['validation'] for a in receipt['attempts']]})
(fixture.OUT/'authority-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
