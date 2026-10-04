"""Independent frozen-v2/frozen-v3 replay of copied actual records."""
import ast,hashlib,json,os,pathlib,shutil,subprocess,sys,tempfile
from unittest.mock import patch
import fixture
d=fixture.d
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.name!='.lock'}
if len(sys.argv)>1:
 # Use this process's explicitly selected source, not fixture's default import.
 raise AssertionError('Use the inline replay command selected below')
old=fixture.PRIVATE/'legacy-source'
for name in subprocess.check_output(['git','ls-tree','-r','--name-only','2fe870d','gflo'],cwd=fixture.BASE,text=True).splitlines():
 p=old/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show','2fe870d:'+name],cwd=fixture.BASE))
def functions(path):return {n.name:ast.get_source_segment(path.read_text(),n) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
old_functions=functions(old/'gflo/documents.py');new_functions=functions(fixture.FROZEN/'gflo/documents.py')
same={}
for name in ['validate_answer','answer_request','repair_request','response_answer','bounded_answer']:
 assert old_functions[name]==new_functions[name];same[name]=hashlib.sha256(new_functions[name].encode()).hexdigest()
code=r'''import json,pathlib,sys
from unittest.mock import patch
from gflo import documents as d
rows=[]
with patch.object(d,'bounded_answer',side_effect=AssertionError('Offline model forbidden')):
 for path in sorted(pathlib.Path(sys.argv[1]).glob('store-*')):
  store=d.DocumentStore(path,executor=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Offline executor forbidden')))
  for record in sorted(path.iterdir()):
   if len(record.name)!=64:continue
   value=store.resolve(record.name);value.pop('age_seconds',None);row={'id':record.name,'resolved':value}
   try:row['replayed']=store.replay(record.name);row['replayed'].pop('age_seconds',None)
   except ValueError as e:row['replay_error']=str(e)
   rows.append(row)
print(json.dumps(rows,sort_keys=True))'''
sources=[fixture.BASE/'.gflo/document-reliability-trial1/store',fixture.BASE/'.gflo/document-research-cohort/json/store',fixture.BASE/'.gflo/document-research-cohort/csv/store']
originals={str(p):hashes(p) for p in sources}
with tempfile.TemporaryDirectory(dir=fixture.PRIVATE) as td:
 root=pathlib.Path(td)
 for n,source in enumerate(sources):shutil.copytree(source,root/f'store-{n}');(root/f'store-{n}').chmod(0o700)
 before=hashes(root);outputs=[]
 for source in [old,fixture.FROZEN]:
  raw=subprocess.check_output([sys.executable,'-c',code,str(root)],env=dict(os.environ,PYTHONPATH=str(source)),cwd=root)
  outputs.append(json.loads(raw));assert hashes(root)==before
 assert outputs[0]==outputs[1]
 counts={}
 for row in outputs[1]:
  receipt=row['resolved']['receipt'];key=str(receipt['format'])+':'+receipt['kind'];counts[key]=counts.get(key,0)+1
 summary={'records':len(outputs[1]),'by_format_kind':counts,'identical_outputs_except_age':True,'original_and_copy_hashes_unchanged':True,'identical_helper_hashes':same,'record_ids':[row['id'] for row in outputs[1]],'failure_replay_errors':[row['replay_error'] for row in outputs[1] if row['resolved']['receipt']['kind']=='answer_failure']}
assert all(hashes(p)==originals[str(p)] for p in sources)
(fixture.OUT/'legacy-results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
