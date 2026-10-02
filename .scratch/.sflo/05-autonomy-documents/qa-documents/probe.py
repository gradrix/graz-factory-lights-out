import contextlib,io,json,pathlib,hashlib,tempfile,copy,subprocess,sys
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path.cwd()))
from gflo.documents import DocumentStore,validate_answer
from gflo.recipes.document import frame
from gflo import guard
from gflo.__main__ import main
OUT=pathlib.Path(__file__).resolve().parent;ROOT=pathlib.Path(tempfile.mkdtemp(prefix='gflo-doc-qa-'));CORPUS=pathlib.Path('.gflo/document-qualification');manifest=pathlib.Path('.scratch/.sflo/05-autonomy-documents/builder-candidate.json');assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='fba3e2f5fe14c640818808b32242c617b7a2ed78c3b2fbb332e7080764b6f336';frozen=json.loads(manifest.read_text())
def integrity():
 for p,h in frozen['files'].items():assert hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h,p
integrity();rows=[];body=b'';kind='text/html';facts=[]
APP={'url':'https://docs.python.org/3.12/library/json.html','source_version':'Synthetic QA fixture; not live documentation','question':'Which separators remove separator whitespace?'}
def executor(args,name,timeout,**kw):
 if args[-1]=='fetch':
  data=frame({'url':APP['url'],'status':200,'content_type':kind,'charset':'utf-8','cache_control':'public, max-age=600','connected':'1.1.1.1','body_size':len(body),'http_headers':{'content-type':kind+'; charset=utf-8','cache-control':'public, max-age=600','content-length':str(len(body))}},body)
  kw['output'].write(data);pathlib.Path(kw['inspect_path']).write_text(json.dumps({'QA':'local framed bytes; no network'}));return {'exit_code':0,'output':''}
 result=guard.run(args,name,timeout,**kw);facts.append(json.loads(pathlib.Path(kw['inspect_path']).read_text()));return result
store=DocumentStore(ROOT/'store',executor=executor)
def save():(OUT/'results.json').write_text(json.dumps({'candidate_manifest':hashlib.sha256(manifest.read_bytes()).hexdigest(),'root':str(ROOT),'rows':rows,'actual_extraction_executors':facts},indent=2)+'\n')
records={}
for c in json.loads((CORPUS/'cases.json').read_text())['cases']:
 body=(CORPUS/c['body']).read_bytes();kind=c['media_type'].split(';')[0];before=set(store.root.iterdir())
 try:e=store.acquire(APP)
 except (ValueError,UnicodeError) as err:
  assert c['outcome'].startswith('reject'),(c['id'],str(err));assert set(store.root.iterdir())==before;rows.append({'case':c['id'],'rejected':str(err)});save();continue
 assert not c['outcome'].startswith('reject');text=' '.join(e['spans'])
 for item in c.get('excluded_fragments',[]):assert item not in text
 fragments=c.get('ordered_visible_fragments',c.get('visible_fragments',[]));positions=[text.index(f) for f in fragments];assert positions==sorted(positions)
 records[c['id']]=e;rows.append({'case':c['id'],'id':e['id'],'spans':e['spans']});save()
e=records['plain'];span=next((i,t) for i,t in enumerate(e['spans'],1) if 'remove separator' in t)
valid={'status':'supported','claims':[{'text':'Compact separators are comma and colon without separator whitespace.','citations':[{'evidence_id':e['id'],'span':span[0],'excerpt':span[1]}]}],'reason':''}
class Client:
 config={'model':'qa-mock'};endpoint='http://127.0.0.1:1'
 def request(self,path,request,**kwargs):
  assert path=='/v1/chat/completions' and 'tools' not in request and request['max_tokens']==2048 and request['reasoning_effort']=='medium' and request['thinking_budget_tokens']==512
  assert kwargs=={'timeout':120,'max_response_bytes':65536};(OUT/'mock-request.json').write_text(json.dumps(request,indent=2)+'\n')
  return {'choices':[{'message':{'content':json.dumps(valid)}}]}
saved=store.answer(e['id'],Client());assert saved['source_url']==APP['url'];assert saved['freshness'].startswith('historical');assert DocumentStore(store.root).replay(saved['id'])['answer']==valid
config=ROOT/'config.json';config.write_text('{}')
with patch('gflo.__main__.ModelWorker',return_value=Client()),contextlib.redirect_stdout(io.StringIO()) as capture:assert main(['--config',str(config),'documents','--store',str(store.root),'answer',e['id']])==0
cli_answer=json.loads(capture.getvalue());assert cli_answer['answer']==valid
with patch('gflo.__main__.ModelWorker',side_effect=AssertionError('inference in replay')),patch('gflo.documents.guard.run',side_effect=AssertionError('fetch in replay')),contextlib.redirect_stdout(io.StringIO()) as capture:assert main(['--config','/absent','documents','--store',str(store.root),'replay',saved['id']])==0
assert json.loads(capture.getvalue())['answer']==valid
rows.append({'case':'answer-child/CLI/restart/offline-replay','passed':True,'answer_id':saved['id']});save()
for label,change in [('id',{'evidence_id':'0'*64}),('span',{'span':999}),('excerpt',{'excerpt':'invented quote'}),('model-url',{'url':'https://unapproved.invalid/'})]:
 v=copy.deepcopy(valid);v['claims'][0]['citations'][0].update(change)
 try:validate_answer(v,e)
 except ValueError:pass
 else:raise AssertionError(label+' accepted')
rows.append({'case':'fabricated-citations','passed':True})
unsupported={'status':'insufficient_evidence','claims':[],'reason':'No future release date is present.'};assert validate_answer(unsupported,e)==unsupported
v=copy.deepcopy(valid);v['claims'][0]['text']='Python 4.0 releases in 2099.';assert validate_answer(v,e)==v;rows.append({'case':'exact-citation-unsupported-claim','structural':'passes provenance','semantic':'fails support; intentional independent semantic gate'})
# Tamper actual evidence bytes, preserve modes, then restore; replay must not silently use saved answer.
f=store.root/e['id']/'body';original=f.read_bytes();f.chmod(0o644);f.write_bytes(b'wrong');f.chmod(0o444)
try:DocumentStore(store.root).replay(saved['id'])
except ValueError:pass
else:raise AssertionError('tampered replay passed')
f.chmod(0o644);f.write_bytes(original);f.chmod(0o444);assert store.replay(saved['id'])['answer']==valid
rows.append({'case':'tampered replay/control restored','passed':True});integrity();save();print('PASS corpus actual extraction, child answer, CLI replay, citations, tamper')
