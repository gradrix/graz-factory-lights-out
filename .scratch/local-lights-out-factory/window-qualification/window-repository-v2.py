import ast,hashlib,json
from pathlib import Path
from gflo.broker import SourceBundle,DockerBroker
from gflo.controller import RunPlan,Controller,prepare_run
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile,LocalModel
from gflo.records import WorkAtom
from gflo.worker import InputSnapshot
from gflo.gates import ProcessCase,ProcessGate
root=Path('.gflo/evidence/window-repository-v2');module='gflo/repository.py'
files={p:Path(p).read_text() for p in ['gflo/__init__.py',module,'gflo/artifacts.py','gflo/broker.py','gflo/records.py','gflo/storage.py']};source=SourceBundle(files=files)
def remainder(text):
 tree=ast.parse(text)
 for cls in tree.body:
  if isinstance(cls,ast.ClassDef) and cls.name=='Repository':cls.body=[n for n in cls.body if not isinstance(n,ast.FunctionDef) or n.name!='read']
 return hashlib.sha256(ast.dump(tree).encode()).hexdigest()
check='''import ast,hashlib,tempfile
from pathlib import Path
from gflo.repository import Repository,RepositoryError,SnapshotSource,snapshot_bundle
from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
class Untouched:
 def _entry(self,path):raise AssertionError('invalid inputs reached source access')
for field in ['start_line','max_lines','max_bytes']:
 for value in [True,False,1.5,1.0,'1',None,[],{},type('SubInt',(int,),{})(5)]:
  try:Repository.read(Untouched(),'file.py',**{field:value})
  except RepositoryError:pass
  else:raise AssertionError((field,value))
with tempfile.TemporaryDirectory() as directory:
 store=ArtifactStore(Path(directory)/'artifacts')
 source=snapshot_bundle(store,SourceBundle(files={'file.py':'first\\nsecond\\nthird\\n'}))
 repo=Repository(SnapshotSource(store,source))
 assert repo.read('file.py',start_line=2,max_lines=1).content=='second\\n'
 assert repo.read('file.py').content=='first\\nsecond\\nthird\\n'
 for field,value in [('start_line',0),('max_lines',0),('max_lines',10001),('max_bytes',0),('max_bytes',1048577)]:
  try:repo.read('file.py',**{field:value})
  except RepositoryError:pass
  else:raise AssertionError((field,value))
tree=ast.parse(Path('gflo/repository.py').read_text())
for cls in tree.body:
 if isinstance(cls,ast.ClassDef) and cls.name=='Repository':cls.body=[n for n in cls.body if not isinstance(n,ast.FunctionDef) or n.name!='read']
assert hashlib.sha256(ast.dump(tree).encode()).hexdigest()==REMAINDER
for path,digest in OTHERS.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
print('repository-window-ok')
'''.replace('REMAINDER',repr(remainder(files[module]))).replace('OTHERS',repr({p:hashlib.sha256(c.encode()).hexdigest() for p,c in files.items() if p!=module}))
gate=ProcessGate(cases=(ProcessCase(command=('python','-c',check),expected_stdout='repository-window-ok\n'),))
fixture=json.loads(Path('.scratch/local-lights-out-factory/leds-modes-fixture.json').read_text());profile=ModelProfile.model_validate_json(json.dumps(fixture['policy']['model_profile'])).model_copy(update={'profile_id':'vllm-python-worker-windows-v1'})
fields=json.loads(Path('examples/work-atom.json').read_text());fields.update(atom_id='window-repository-v2',objective='In gflo/repository.py Repository.read, require start_line, max_lines and max_bytes to be actual built-in ints (type is int), rejecting booleans and all other types with RepositoryError before range comparisons or source access. Preserve existing numeric bounds, valid reads and all other methods. Use the existing error message. Edit only this method.',requirement_ids=['read-inputs'],writable_paths=[module],prohibited_paths=[],required_gates=[{'gate_id':'input-validation-preservation','validator_digest':gate.digest()}],max_attempts=2,context_budget={'total_tokens':12288,'output_tokens':4096});fields['inputs_digest']=InputSnapshot(source_digest=source.digest(),source_revision=fields['source_revision']).digest();atom=WorkAtom.model_validate_json(json.dumps(fields))
plan=RunPlan(atom=atom,source=source,gates={'input-validation-preservation':gate},model_profile=profile,deployment=fixture['policy']['deployment'],broker_image=fixture['request']['environments']['python']['image'],selected_paths=(module,))
(root/'plan.json').write_text(plan.canonical()+'\n')
with WorkLedger(root/'ledger.db') as ledger:
 prepare_run(ledger,plan);result=Controller(ledger,LocalModel(ledger.artifacts,profile),DockerBroker(ledger.artifacts,plan.broker_image)).run(atom.atom_id)
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)
