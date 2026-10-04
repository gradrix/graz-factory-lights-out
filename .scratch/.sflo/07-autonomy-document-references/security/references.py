"""Independent bounded-reference tests against frozen92deaab; no model or rig."""
import copy,json,pathlib,tempfile
from unittest.mock import patch
import fixture
d=fixture.d
import gflo.document_references as r
rows=[]
def selected(ids=[1],text='Claim'):
 return {'status':'supported','claims':[{'text':text,'spans':ids}],'reason':''}
def evidence(spans):return {'id':'a'*64,'spans':spans,'receipt':{'approval':{'source_version':'controlled'},'retrieved_utc':'2026-10-04T00:00:00+00:00'}}
class Unexpanded(list):
 def __getitem__(self,key):raise AssertionError('Expanded before all checks')
bad={}
for value in [True,False,0,-1,2,1.0,'1',None]:bad['id-'+repr(value)]=selected([value])
bad.update({'refs-empty':selected([]),'refs-five':selected([1]*5),'claims-nine':dict(selected(),claims=[selected()['claims'][0]]*9),'occurrences17':dict(selected(),claims=[selected([1]*4)['claims'][0]]*4+[selected()['claims'][0]]),'old-citation-field':dict(selected(),claims=[{'text':'Claim','spans':[1],'excerpt':'forged'}]),'extra-evidence':dict(selected(),evidence_id='b'*64),'late-invalid-id':dict(selected(),claims=[selected()['claims'][0],selected([0])['claims'][0]])})
for name,value in bad.items():
 error=None
 try:r.materialize(value,evidence(Unexpanded(['source'])))
 except ValueError as e:error=str(e)
 assert error;rows.append({'case':name,'refused_before_expansion':True,'error':error})
for name,text,limit in [('ascii-claim','x'*1022,1024),('astral-claim','😀'*85+'aa',1024),('control-claim','\x01'*170+'aa',1024),('ascii-span','x'*2046,2048),('astral-span','😀'*170+'aaaaaa',2048),('control-span','\x01'*341,2048),('ascii-reason','x'*2046,2048),('astral-reason','😀'*170+'aaaaaa',2048)]:
 assert len(d.encoded(text))==limit
 for extra in ['', 'x']:
  value=selected(text=text+extra) if 'claim' in name else selected()
  src=evidence([text+extra] if 'span' in name else ['ordinary'])
  if 'reason' in name:value={'status':'insufficient_evidence','claims':[],'reason':text+extra}
  error=None
  try:result=r.materialize(value,src)
  except ValueError as e:error=str(e)
  assert bool(error)==bool(extra)
  rows.append({'case':name+('plus1' if extra else '-at-cap'),'encoded_size':len(d.encoded(text+extra)),'accepted':error is None,'error':error})
maximum={'status':'supported','claims':[{'text':'x'*1022,'spans':[2048,2048]} for _ in range(8)],'reason':''}
expanded=r.materialize(maximum,evidence(['x']*2047+['y'*2046]));assert len(d.encoded(expanded))==42893
rows.append({'case':'maximum-legal-repeated-expansion','claims':8,'occurrences':16,'encoded_answer_bytes':len(d.encoded(expanded))})
for size in [12*1024,12*1024+1]:
 value={'padding':''};value['padding']='x'*(size-len(d.encoded(value)));error=None
 try:r.check_receipt_bounds(value)
 except ValueError as e:error=str(e)
 assert bool(error)==(size>12*1024);rows.append({'case':'metadata-'+str(size),'error':error})
for size in [48*1024,48*1024+1]:
 value={'answer':{'padding':''}};value['answer']['padding']='x'*(size-len(d.encoded(value['answer'])));error=None
 try:r.check_receipt_bounds(value)
 except ValueError as e:error=str(e)
 assert bool(error)==(size>48*1024);rows.append({'case':'canonical-defense-'+str(size),'error':error,'synthetic_serializer_control':True})
for mode in ['unicode-exact','long-selected-to-insufficient','long-unselected-supported','all-eligible-insufficient','cancel-before-repair','final-cancel']:
 with tempfile.TemporaryDirectory(dir=fixture.PRIVATE) as td:
  store,ev,client,unused=fixture.fixture(pathlib.Path(td));cancel=[False];calls=[]
  if mode.startswith('long-'):
   # New immutable evidence identity for this deliberately overlong source.
   source=store.root/ev['id'];receipt=copy.deepcopy(ev['receipt']);stage=pathlib.Path(tempfile.mkdtemp(prefix='.stage-',dir=store.root))
   spans=['x'*2047,'The writer won’t change.'];raw=d.encoded(spans)
   d.write_file(stage/'body',(source/'body').read_bytes());d.write_file(stage/'text',raw);receipt.update(text_sha256=d.digest(raw),text_size=len(raw));ev=store._publish(stage,receipt,lambda:False)
  values=[selected([3]) if mode=='unicode-exact' else selected()]
  if mode=='long-selected-to-insufficient':values=[selected(),{'status':'insufficient_evidence','claims':[],'reason':'Cannot cite required text.'}]
  if mode=='long-unselected-supported':values=[selected([2])]
  if mode=='all-eligible-insufficient':values=[{'status':'insufficient_evidence','claims':[],'reason':'Not in these spans.'}]
  if mode=='cancel-before-repair':values=[selected([0])]
  def call(*a,**kw):calls.append(True);return fixture.response(values[len(calls)-1])
  original_response=r.reference_response
  def response(*a):
   value=original_response(*a)
   if mode=='cancel-before-repair':cancel[0]=True
   return value
  original_sync=d.sync_directory
  def sync(path):
   original_sync(path)
   if mode=='final-cancel' and not (path/'pending').exists():cancel[0]=True
  initial=fixture.ids(store);error=None;result=None
  with patch.object(d,'bounded_answer',call),patch.object(r,'reference_response',response),patch.object(d,'sync_directory',sync):
   try:result=store.answer(ev['id'],client,cancelled=lambda:cancel[0])
   except ValueError as e:error=e
  if mode=='long-selected-to-insufficient':
   assert isinstance(error,d.AnswerFailure) and len(calls)==2;record=store.resolve(error.identifier);assert 'capacity unresolved' in record['receipt']['attempts'][1]['error']
   try:store.replay(error.identifier)
   except ValueError:pass
   else:raise AssertionError('Capacity failure replayed')
  elif mode in ['cancel-before-repair','final-cancel']:assert error and len(calls)==1 and fixture.ids(store)==initial
  else:
   assert result and len(calls)==1
   if mode=='unicode-exact':assert result['answer']['claims'][0]['citations'][0]['excerpt']==ev['spans'][2]
   if mode=='long-unselected-supported':assert result['answer']['claims'][0]['citations'][0]['excerpt']=='The writer won’t change.'
  rows.append({'case':mode,'calls':len(calls),'error':str(error) if error else None,'status':result['answer']['status'] if result else None,'published_count':len(fixture.ids(store)-initial)})
(fixture.OUT/'reference-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'reference/boundary cases')
