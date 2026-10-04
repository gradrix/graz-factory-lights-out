"""Bounded response/receipt controls using actual disposable fake-client children."""
import copy,json,pathlib,tempfile,time
from unittest.mock import patch
import probe
d=probe.d;rows=[]
class Client:
 config={'model':'local'};endpoint='http://127.0.0.1:1'
 def __init__(self,values,root):self.values=values;self.root=root
 def request(self,path,request,**kwargs):
  log=self.root/'calls';number=len(log.read_text().splitlines()) if log.exists() else 0
  with log.open('a') as stream:stream.write(json.dumps({'path':path,'limits':kwargs})+'\n')
  value=self.values[number]
  if value=='sleep':time.sleep(30)
  return value
for mode in ['near-response-bound','response-bound-plus-one','two-large-invalid','shortened-total-deadline','canonical-receipt-overflow']:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  root=pathlib.Path(td);store,evidence,unused,answer=probe.fixture(root)
  values=[probe.response(answer)]
  if mode in ['near-response-bound','response-bound-plus-one','two-large-invalid']:
   target=65523+(mode=='response-bound-plus-one')
   value=probe.response('{bad' if mode=='two-large-invalid' else answer);value['padding']=''
   value['padding']='x'*(target-len(d.encoded(value)));assert len(d.encoded(value))==target
   values=[value,value] if mode=='two-large-invalid' else [value]
  if mode=='shortened-total-deadline':values=['sleep']
  if mode=='canonical-receipt-overflow':
   answer['claims']=[copy.deepcopy(answer['claims'][0]) for _ in range(16)]
   for claim in answer['claims']:claim['text']='x'*4000
   value=probe.response(answer)
   while len(d.encoded(value))>65523:answer['claims'][-1]['text']=answer['claims'][-1]['text'][:-1];value=probe.response(answer)
   values=[value]
  client=Client(values,root);error=None;saved=None;started=time.monotonic()
  with patch.object(d,'ANSWER_SECONDS',11.25 if mode=='shortened-total-deadline' else 260):
   try:saved=store.answer(evidence['id'],client)
   except d.AnswerFailure as e:error=e;saved=store.resolve(e.identifier)
  elapsed=time.monotonic()-started;calls=(root/'calls').read_text().splitlines();receipt=store.resolve(saved['id'])['receipt'];sizes=probe.pathsizes(store,saved['id'])
  assert all(n<=65536 for n in sizes.values()) and sum(sizes.values())<=192*1024
  if mode=='near-response-bound':assert error is None and sizes['response-1.json']==65523
  elif mode=='two-large-invalid':assert error and len(calls)==2 and sizes['response-1.json']==sizes['response-2.json']==65523
  else:assert error and len(calls)==1
  if mode=='shortened-total-deadline':assert elapsed<2
  if mode=='canonical-receipt-overflow':assert receipt['failure']=='Canonical answer exceeds receipt bound' and receipt['attempts'][0]['validation']=='valid'
  rows.append({'case':mode,'calls':len(calls),'elapsed_s':elapsed,'sizes':sizes,'kind':receipt['kind'],'failure':receipt.get('failure'),'attempts':receipt['attempts'],'actual_fake_child':True})
(probe.OUT/'resource-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
