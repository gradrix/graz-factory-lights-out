"""Independent no-model public answer probe through actual bounded fork children."""
import hashlib,json,pathlib,sys,tempfile
ROOT=pathlib.Path.cwd();sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from gflo import documents
from test_documents import DocumentsTests,APPROVAL
manifest=ROOT/'.scratch/.sflo/07-autonomy-document-references/builder-candidate.json'
def frozen():
 assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='acd723171fe9b3f5ce9b90b2dc8aea29dbb5e57d41854cf322798690556bc698'
 for n,h in json.loads(manifest.read_text())['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
frozen();results=[]
with tempfile.TemporaryDirectory() as tmp:
 root=pathlib.Path(tmp);fixture=DocumentsTests();fixture.body='<p>It isn’t an invented quote.</p>'.encode();store=documents.DocumentStore(root/'store',executor=fixture.executor);evidence=store.acquire(APPROVAL)
 answer={'status':'supported','claims':[{'text':'The source has curly punctuation.','spans':[1,1]}],'reason':''}
 from gflo.document_references import reference_request,materialize
 canonical=materialize(answer,evidence)
 class Client:
  config={'model':'local'};endpoint='http://127.0.0.1:18000'
  def request(self,path,body=None,timeout=120,*,max_response_bytes=None):
   assert path=='/v1/chat/completions' and max_response_bytes==65536 and timeout<=120
   files=list(calls.glob('*.json'));number=len(files)+1
   (calls/f'{number}.json').write_text(json.dumps(body))
   content=json.dumps({'status':'supported','claims':[{'text':'Bad bool selector','spans':[True]}],'reason':''}) if number==1 or mode=='exhaust' else json.dumps(answer)
   return {'choices':[{'message':{'content':content}}]}
 for mode in ['repair','exhaust']:
  calls=root/mode;calls.mkdir()
  try:saved=store.answer(evidence['id'],Client());identifier=saved['id'];assert mode=='repair'
  except documents.AnswerFailure as error:identifier=error.identifier;assert mode=='exhaust'
  record=store.resolve(identifier);rec=record['receipt'];assert len(rec['attempts'])==2;assert len(list(calls.glob('*.json')))==2
  for n in [1,2]:assert (store.root/identifier/f'response-{n}.json').exists()
  if mode=='repair':
   assert store.replay(identifier)['answer']==canonical and rec['format']==3
   first=json.loads((calls/'1.json').read_text());assert first==reference_request(evidence,'local',evidence['receipt']['approval']['question'])
   assert rec['attempts'][0]['request_sha256']==documents.digest(documents.encoded(first))
   assert canonical['claims'][0]['citations'][0]['excerpt']=='It isn’t an invented quote.'
   assert len(canonical['claims'][0]['citations'])==2
  else:
   try:store.replay(identifier)
   except ValueError:pass
   else:raise AssertionError('Failure replayed')
  results.append({'mode':mode,'kind':rec['kind'],'attempt_validation':[x['validation']for x in rec['attempts']],'two_actual_bounded_children':True})
frozen();(ROOT/'.scratch/.sflo/07-autonomy-document-references/qa/probe-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
