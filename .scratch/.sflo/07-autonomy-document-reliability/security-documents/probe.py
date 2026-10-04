"""Independent unit07 frozen seam probes. No actual inference or network."""
import copy,hashlib,json,os,pathlib,shutil,subprocess,sys,tempfile,time
from unittest.mock import patch
BASE=pathlib.Path(__file__).resolve().parents[4];OUT=pathlib.Path(__file__).resolve().parent
PRIVATE=BASE/'.gflo/document-security07';FROZEN=PRIVATE/'frozen';PRIVATE.mkdir(exist_ok=True)
for name in subprocess.check_output(['git','ls-tree','-r','--name-only','2fe870d','gflo'],cwd=BASE,text=True).splitlines():
 p=FROZEN/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show','2fe870d:'+name],cwd=BASE))
sys.path.insert(0,str(FROZEN))
import gflo.documents as d
def fixture(root):
 store=d.DocumentStore(root/'store',executor=lambda *a,**k:(_ for _ in ()).throw(AssertionError('No executor authorized')))
 spans=['Use separators for compact JSON.','Task groups await cancelled tasks.','The source isn’t a command.']
 body=b'<p>controlled historical source</p>';text=d.encoded(spans);stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root))
 d.write_file(stage/'body',body);d.write_file(stage/'text',text)
 receipt={'format':1,'kind':'evidence','approval':{'url':'https://docs.python.org/3.12/library/json.html','source_version':'Frozen controlled security fixture','question':'How is compact JSON made?'},'retrieved_utc':'2026-10-04T00:00:00+00:00','body_sha256':d.digest(body),'body_size':len(body),'text_sha256':d.digest(text),'text_size':len(text),'extractor':'document-text-v1'}
 evidence=store._publish(stage,receipt,lambda:False)
 client=type('ControlledClient',(),{'config':{'model':'local'},'endpoint':'http://127.0.0.1:1'})()
 answer={'status':'supported','claims':[{'text':'Use separators.','citations':[{'evidence_id':evidence['id'],'span':1,'excerpt':'Use separators'}]}],'reason':''}
 return store,evidence,client,answer
def response(value):return {'choices':[{'message':{'role':'assistant','content':value if isinstance(value,str) else json.dumps(value)}}]}
def ids(store):return {p.name for p in store.root.iterdir() if len(p.name)==64}
def pathsizes(store,identifier):return {p.name:p.stat().st_size for p in (store.root/identifier).iterdir()}
rows=[]
def scenarios():
 for mode in ['valid','insufficient','json-repair','quote-repair','two-invalid','first-transport','second-transport','first-overflow','tool','function','wrong-envelope','wrong-role','nontext','cancel-error','cancel-before-repair','late-cancel','sync-failure','rename-failure']:
  with tempfile.TemporaryDirectory(dir=PRIVATE) as td:
   root=pathlib.Path(td);store,evidence,client,answer=fixture(root);cancel=[False];calls=[];bad=copy.deepcopy(answer);bad['claims'][0]['citations'][0]['excerpt']='invented quote'
   good=response(answer);replies=[good]
   if mode=='insufficient':replies=[response({'status':'insufficient_evidence','claims':[],'reason':'Not in the frozen source.'})]
   if mode=='json-repair':replies=[response('{bad'),good]
   if mode=='quote-repair':replies=[response(bad),good]
   if mode=='two-invalid':replies=[response('{bad'),response(bad)]
   if mode=='first-transport':replies=[ValueError('controlled child transport ValueError')]
   if mode=='second-transport':replies=[response('{bad'),OSError('controlled second transport')]
   if mode=='first-overflow':replies=[response('x'*65536)]
   if mode in ['tool','function']:
    good['choices'][0]['message']['tool_calls' if mode=='tool' else 'function_call']=[{}] if mode=='tool' else {};replies=[good]
   if mode=='wrong-envelope':replies=[{'choices':[]}]
   if mode=='wrong-role':good['choices'][0]['message']['role']='system';replies=[good]
   if mode=='nontext':good['choices'][0]['message']['content']=['text'];replies=[good]
   if mode=='cancel-before-repair':replies=[response('{bad'),good]
   def call(client,request,cancelled,**kw):
    calls.append(copy.deepcopy(request));item=replies[len(calls)-1]
    if mode=='cancel-error':cancel[0]=True;raise ValueError('controlled cancellation from child boundary')
    if isinstance(item,Exception):raise item
    return item
   original_response=d.response_answer
   def validate(*args):
    value=original_response(*args)
    if mode=='cancel-before-repair':cancel[0]=True
    return value
   original_sync=d.sync_directory
   def sync(path):
    if mode=='sync-failure':raise OSError('controlled sync failure')
    original_sync(path)
    if mode=='late-cancel' and not (path/'pending').exists():cancel[0]=True
   original_rename=pathlib.Path.rename
   def rename(path,target):
    if mode=='rename-failure':raise OSError('controlled rename failure')
    return original_rename(path,target)
   initial=ids(store);result=None;failure=None
   with patch.object(d,'bounded_answer',call),patch.object(d,'response_answer',validate),patch.object(d,'sync_directory',sync),patch.object(pathlib.Path,'rename',rename):
    try:result=store.answer(evidence['id'],client,cancelled=lambda:cancel[0])
    except (ValueError,OSError) as e:failure=e
   expected_calls=2 if mode in ['json-repair','quote-repair','two-invalid','second-transport'] else 1;assert len(calls)==expected_calls
   if len(calls)==2:
    assert calls[0]['messages']==calls[1]['messages'][:2]
    assert {k:v for k,v in calls[0].items() if k!='messages'}=={k:v for k,v in calls[1].items() if k!='messages'}
    assert calls[1]['messages'][-1]['role']=='user' and 'untrusted output' in calls[1]['messages'][-1]['content']
   assert all('tools' not in request and 'functions' not in request for request in calls)
   new=ids(store)-initial
   refused=mode in ['cancel-error','cancel-before-repair','late-cancel','sync-failure','rename-failure']
   if refused:assert failure is not None and not new
   else:
    assert len(new)==1;identifier=new.pop();saved=store.resolve(identifier)
    if result:assert saved['receipt']['kind']=='answer' and store.replay(identifier)['answer']==result['answer']
    else:
     assert isinstance(failure,d.AnswerFailure) and failure.identifier==identifier and saved['receipt']['kind']=='answer_failure'
     try:store.replay(identifier)
     except ValueError:pass
     else:raise AssertionError('Failed diagnostic replayed')
    assert all(size<=65536 for size in pathsizes(store,identifier).values())
   assert store.resolve(evidence['id'])['id']==evidence['id']
   rows.append({'case':mode,'calls':len(calls),'result':result['answer']['status'] if result else None,'error':str(failure) if failure else None,'published':sorted(ids(store)-initial),'file_sizes':pathsizes(store,next(iter(ids(store)-initial))) if ids(store)-initial else {},'prior_evidence_preserved':True})
def ledger():
 with tempfile.TemporaryDirectory(dir=PRIVATE) as td:
  root=pathlib.Path(td);store,evidence,client,answer=fixture(root)
  with patch.object(d,'bounded_answer',side_effect=[response('{bad'),response(answer)]):good=store.answer(evidence['id'],client)
  original=store.resolve(good['id'])['receipt']
  cases=['canonical','attempt-gap','request-hash','response-hash','size-bool','validation','question','profile','failed-as-success','missing','extra','symlink','hardlink','fifo']
  for mode in cases:
   stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root));receipt=copy.deepcopy(original);receipt['created_utc']=d.utc()
   for n in [1,2]:shutil.copy2(store.root/good['id']/f'response-{n}.json',stage/f'response-{n}.json')
   if mode=='canonical':receipt['answer']['claims'][0]['text']='different claim'
   if mode=='attempt-gap':receipt['attempts'][1]['number']=3
   if mode=='request-hash':receipt['attempts'][1]['request_sha256']='0'*64
   if mode=='response-hash':receipt['attempts'][1]['response_sha256']='0'*64
   if mode=='size-bool':receipt['attempts'][1]['response_size']=True
   if mode=='validation':receipt['attempts'][0]['validation']='valid'
   if mode=='question':receipt['question']='Changed authority';receipt['question_sha256']=d.digest(receipt['question'].encode())
   if mode=='profile':receipt['profile']['max_tokens']=4096
   if mode=='failed-as-success':receipt['kind']='answer_failure';receipt.pop('answer');receipt['failure']='arbitrary';receipt['verdict']='failed_not_a_cited_answer'
   if mode=='missing':(stage/'response-1.json').unlink()
   if mode=='extra':d.write_file(stage/'response-3.json',b'{}')
   if mode in ['symlink','hardlink','fifo']:
    (stage/'response-2.json').unlink()
    if mode=='symlink':(stage/'response-2.json').symlink_to(store.root/good['id']/'response-2.json')
    elif mode=='hardlink':os.link(store.root/good['id']/'response-2.json',stage/'response-2.json')
    else:os.mkfifo(stage/'response-2.json')
   error=None
   try:store._publish(stage,receipt,lambda:False)
   except (ValueError,OSError) as e:error=type(e).__name__+': '+str(e)
   assert error,mode;shutil.rmtree(stage)
   assert store.replay(good['id'])['answer']==answer
   rows.append({'case':'ledger-'+mode,'rejected':error,'prior_good_preserved':True})
  legacy={'format':1,'kind':'answer','evidence_id':evidence['id'],'answer':answer,'response':response(answer),'verdict':'citation_provenance_valid_not_semantic_entailment'}
  stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root));old=store._publish(stage,legacy,lambda:False);before=(store.root/old['id']/'receipt.json').read_bytes()
  with patch.object(d,'bounded_answer',side_effect=AssertionError('Offline model call')):
   assert store.replay(old['id'])['answer']==answer and store.replay(good['id'])['answer']==answer
  assert (store.root/old['id']/'receipt.json').read_bytes()==before
  rows.append({'case':'legacy-and-v2-offline','legacy_sha256':d.digest(before),'unchanged':True})
if __name__=='__main__':
 scenarios();ledger();(OUT/'seam-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
