"""Rehashed format3 tamper and final-publication checks."""
import copy,json,pathlib,shutil,tempfile
from unittest.mock import patch
import fixture
d=fixture.d;rows=[]
selected={'status':'supported','claims':[{'text':'Claim','spans':[1]}],'reason':''}
with tempfile.TemporaryDirectory(dir=fixture.PRIVATE) as td:
 store,ev,client,unused=fixture.fixture(pathlib.Path(td))
 with patch.object(d,'bounded_answer',return_value=fixture.response(selected)):good=store.answer(ev['id'],client)
 original=store.resolve(good['id'])['receipt']
 for mode in ['catalog','limits','canonical-excerpt','canonical-source','canonical-span','raw-selection','request-hash','format-bool','format-unknown','downgrade-format2','extra-file']:
  receipt=copy.deepcopy(original);receipt['created_utc']=d.utc();stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root));raw=(store.root/good['id']/'response-1.json').read_bytes()
  if mode=='catalog':receipt['protocol']['catalog_sha256']='0'*64
  if mode=='limits':receipt['protocol']['limits']['reference_occurrences']=128
  if mode=='canonical-excerpt':receipt['answer']['claims'][0]['citations'][0]['excerpt']='Use separators'
  if mode=='canonical-source':receipt['answer']['claims'][0]['citations'][0]['evidence_id']='0'*64
  if mode=='canonical-span':receipt['answer']['claims'][0]['citations'][0]['span']=2
  if mode=='raw-selection':
   changed=copy.deepcopy(selected);changed['claims'][0]['spans']=[2];raw=d.encoded(fixture.response(changed));receipt['attempts'][0].update(response_sha256=d.digest(raw),response_size=len(raw))
  if mode=='request-hash':receipt['attempts'][0]['request_sha256']='0'*64
  if mode=='format-bool':receipt['format']=True
  if mode=='format-unknown':receipt['format']=4
  if mode=='downgrade-format2':receipt['format']=2;receipt.pop('protocol')
  d.write_file(stage/'response-1.json',raw)
  if mode=='extra-file':d.write_file(stage/'response-2.json',raw)
  error=None
  try:store._publish(stage,receipt,lambda:False)
  except ValueError as e:error=str(e)
  assert error,mode;shutil.rmtree(stage);assert store.replay(good['id'])['answer']==good['answer']
  rows.append({'case':mode,'rejected':error,'prior_good_preserved':True})
for mode in ['success','failed-diagnostic']:
 with tempfile.TemporaryDirectory(dir=fixture.PRIVATE) as td:
  store,ev,client,unused=fixture.fixture(pathlib.Path(td));committed=[False];attempted=[];rename=pathlib.Path.rename;read=d.checked_file;write=d.write_file;remove=d.shutil.rmtree;render=store._replay
  def moved(path,target):result=rename(path,target);committed[0]=True;return result
  def guard(name,fn):
   def invoke(*args,**kw):
    if committed[0]:attempted.append(name);raise AssertionError('Postcommit '+name)
    return fn(*args,**kw)
   return invoke
  with patch.object(d,'bounded_answer',return_value=fixture.response(selected if mode=='success' else '{bad')),patch.object(pathlib.Path,'rename',moved),patch.object(d,'checked_file',guard('read',read)),patch.object(d,'write_file',guard('write',write)),patch.object(d.shutil,'rmtree',guard('cleanup',remove)),patch.object(store,'_replay',guard('render',render)):
   try:result=store.answer(ev['id'],client);assert mode=='success'
   except d.AnswerFailure:assert mode=='failed-diagnostic'
  assert committed[0] and not attempted;rows.append({'case':'postcommit-'+mode,'committed':True,'postcommit_operations':attempted})
(fixture.OUT/'ledger-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'ledger/publication cases')
