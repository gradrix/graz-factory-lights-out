"""Actual preserved records via private copies; no model or container calls."""
import hashlib,json,pathlib,shutil,sys,tempfile
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path.cwd()))
from gflo.documents import DocumentStore
sources={'format2':pathlib.Path('.gflo/document-reliability-trial1/store'),'format1':pathlib.Path('.gflo/document-rig-trial-1/store')}
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p!=root/'.lock'}
rows=[]
with tempfile.TemporaryDirectory() as tmp:
 for group,source in sources.items():
  before=hashes(source);dest=pathlib.Path(tmp)/group;shutil.copytree(source,dest);store=DocumentStore(dest)
  with patch('gflo.documents.bounded_answer',side_effect=AssertionError('Forbidden inference')):
   for path in sorted(dest.iterdir()):
    if not path.is_dir() or len(path.name)!=64:continue
    record=store.resolve(path.name);kind=record['receipt']['kind'];row={'group':group,'id':path.name,'kind':kind,'format':record['receipt']['format']}
    if kind=='answer':assert store.replay(path.name)['answer']==record['receipt']['answer'];row['replayed']=True
    elif kind=='answer_failure':
     try:store.replay(path.name)
     except ValueError as error:assert str(error)=='Replay requires a saved answer ID';row['replay_refused']=True
     else:raise AssertionError('Failure replay accepted')
    rows.append(row)
  assert before==hashes(source)==hashes(dest)
pathlib.Path('.scratch/.sflo/07-autonomy-document-references/qa/legacy-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'actual preserved records, original/copy hashes unchanged')
