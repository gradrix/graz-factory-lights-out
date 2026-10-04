"""Worst arbitrary terminal error at the admitted format3 metadata edge."""
import copy,json,pathlib,tempfile
from unittest.mock import patch
import fixture
d=fixture.d
import gflo.document_references as r
STAMP='2026-10-04T00:00:00.000000+00:00';rows=[]
for mode in ['first-astral-error','second-astral-error','one-byte-over-preflight']:
 with tempfile.TemporaryDirectory(dir=fixture.PRIVATE) as td:
  store,ev,client,unused=fixture.fixture(pathlib.Path(td));question=ev['receipt']['approval']['question'];request=r.reference_request(ev,client.config['model'],question)
  receipt={'format':3,'kind':'answer_failure','created_utc':STAMP,'evidence_id':ev['id'],'question':question,'question_sha256':d.digest(question.encode()),'model':client.config['model'],'config':{'endpoint':client.endpoint,'model':client.config['model']},'profile':{k:v for k,v in request.items() if k!='messages'},'attempts':[],'failure':'No validated answer','verdict':'failed_not_a_cited_answer','protocol':r.protocol(ev)}
  reserve=copy.deepcopy(receipt);reserve.update(failure='\uffff'*512,attempts=[{'number':n,'request_sha256':'f'*64,'response_sha256':'f'*64,'response_size':65536,'validation':'inference_error','error':'\uffff'*512} for n in (1,2)])
  padding=12*1024-len(d.encoded(reserve));assert padding>0
  client.endpoint+='x'*(padding+(mode=='one-byte-over-preflight'));reserve['config']['endpoint']=client.endpoint
  preflight_bytes=len(d.encoded(reserve));assert preflight_bytes==12*1024+(mode=='one-byte-over-preflight')
  calls=[]
  def call(*args,**kw):
   calls.append(True)
   if mode=='second-astral-error' and len(calls)==1:return fixture.response('{bad')
   raise ValueError('😀'*512)
  before=fixture.ids(store);error=None
  with patch.object(d,'bounded_answer',call),patch.object(d,'utc',return_value=STAMP):
   try:store.answer(ev['id'],client)
   except ValueError as e:error=e
  assert error
  if mode=='one-byte-over-preflight':assert not calls and fixture.ids(store)==before;row={'case':mode,'preflight_bytes':preflight_bytes,'calls':0,'published':False,'error':str(error)}
  else:
   assert isinstance(error,d.AnswerFailure);record=store.resolve(error.identifier);receipt=record['receipt'];metadata={k:v for k,v in receipt.items() if k!='answer'}
   assert len(d.encoded(metadata))<=12*1024
   assert receipt['attempts'][-1]['error']=='😀'*512
   assert len(calls)==(2 if mode=='second-astral-error' else 1)
   if mode=='second-astral-error':assert (store.root/error.identifier/'response-1.json').read_bytes()==d.encoded(fixture.response('{bad'))
   row={'case':mode,'preflight_bytes':preflight_bytes,'calls':len(calls),'terminal_error_characters':512,'terminal_error_encoded_bytes':len(d.encoded(receipt['attempts'][-1]['error'])),'actual_metadata_bytes':len(d.encoded(metadata)),'saved_failure':True,'first_response_retained':(store.root/error.identifier/'response-1.json').exists()}
  rows.append(row)
(fixture.OUT/'metadata-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
