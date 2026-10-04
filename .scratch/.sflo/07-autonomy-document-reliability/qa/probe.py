"""Independent no-model public answer probe through actual bounded fork children."""
import hashlib,json,pathlib,sys,tempfile
ROOT=pathlib.Path.cwd();sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from gflo import documents
from test_documents import DocumentsTests,APPROVAL
manifest=ROOT/'.scratch/.sflo/07-autonomy-document-reliability/builder-candidate.json'
def frozen():
 assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='4e1481dede629f9c83be9bbd0002d0975eccbd33820d4456ef5c75bd9eecfc2e'
 for n,h in json.loads(manifest.read_text())['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
frozen();results=[]
with tempfile.TemporaryDirectory() as tmp:
 root=pathlib.Path(tmp);fixture=DocumentsTests();fixture.body=b'<p>Use separators=(comma, colon).</p>';store=documents.DocumentStore(root/'store',executor=fixture.executor);evidence=store.acquire(APPROVAL)
 answer={'status':'supported','claims':[{'text':'Use compact separators.','citations':[{'evidence_id':evidence['id'],'span':1,'excerpt':'separators'}]}],'reason':''}
 class Client:
  config={'model':'local'};endpoint='http://127.0.0.1:18000'
  def request(self,path,body=None,timeout=120,*,max_response_bytes=None):
   assert path=='/v1/chat/completions' and max_response_bytes==65536 and timeout<=120
   files=list(calls.glob('*.json'));number=len(files)+1
   (calls/f'{number}.json').write_text(json.dumps(body))
   content='{invalid' if number==1 or mode=='exhaust' else json.dumps(answer)
   return {'choices':[{'message':{'content':content}}]}
 for mode in ['repair','exhaust']:
  calls=root/mode;calls.mkdir()
  try:saved=store.answer(evidence['id'],Client());identifier=saved['id'];assert mode=='repair'
  except documents.AnswerFailure as error:identifier=error.identifier;assert mode=='exhaust'
  record=store.resolve(identifier);rec=record['receipt'];assert len(rec['attempts'])==2;assert len(list(calls.glob('*.json')))==2
  for n in [1,2]:assert (store.root/identifier/f'response-{n}.json').exists()
  if mode=='repair':assert store.replay(identifier)['answer']==answer
  else:
   try:store.replay(identifier)
   except ValueError:pass
   else:raise AssertionError('Failure replayed')
  results.append({'mode':mode,'kind':rec['kind'],'attempt_validation':[x['validation']for x in rec['attempts']],'two_actual_bounded_children':True})
frozen();(ROOT/'.scratch/.sflo/07-autonomy-document-reliability/qa/probe-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
