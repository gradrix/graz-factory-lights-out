"""Offline replay of copied actual unit05 historical format1 records."""
import hashlib,json,pathlib,shutil,tempfile
from unittest.mock import patch
import probe
d=probe.d;rows=[]
for label in ['csv','json']:
 source=probe.BASE/'.gflo/document-research-cohort'/label/'store'
 def inventory(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.name!='.lock'}
 before=inventory(source)
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  target=pathlib.Path(td)/'store';shutil.copytree(source,target);store=d.DocumentStore(target,executor=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Offline executor used')))
  with patch.object(d,'bounded_answer',side_effect=AssertionError('Offline model used')):
   for record in target.iterdir():
    if len(record.name)!=64:continue
    receipt=json.loads((record/'receipt.json').read_bytes())
    if receipt['kind']!='answer':continue
    assert receipt['format']==1;result=store.replay(record.name)
    assert result['answer']==receipt['answer']
    rows.append({'source':label,'answer_id':record.name,'evidence_id':receipt['evidence_id'],'status':result['answer']['status'],'format':1,'replayed_offline':True})
  assert before==inventory(target)
 assert before==inventory(source)
(probe.OUT/'legacy-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
