import ast,hashlib,json
from pathlib import Path
from gflo.broker import SourceBundle,DockerBroker
from gflo.controller import RunPlan,Controller,prepare_run
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile,LocalModel
from gflo.records import WorkAtom
from gflo.worker import InputSnapshot
from gflo.gates import ProcessCase,ProcessGate
root=Path('.gflo/evidence/window-large-v2')
text=''.join(f'constant_{i} = {i}\n' for i in range(5000))+'def chosen_value():\n    return 41\n'+''.join(f'constant_{i} = {i}\n' for i in range(5000,10000))
consumer='from large import chosen_value\ndef render(value):\n    return "value=" + str(chosen_value(value))\n'
source=SourceBundle(files={'large.py':text,'consumer.py':consumer})
prefix=text[:text.index('def chosen_value')];suffix=text[text.index('constant_5000'):]
check='''import ast,hashlib
from pathlib import Path
from large import chosen_value
from consumer import render
assert chosen_value()==42
for value in range(-250,251):
 assert chosen_value(value)==min(100,max(0,value))
 assert render(value)=='value='+str(min(100,max(0,value)))
for value in [True,False,None,1.0,'42',[],{},type('SubInt',(int,),{})(5)]:
 try:chosen_value(value)
 except TypeError:pass
 else:raise AssertionError(('non-integer accepted',type(value).__name__))
text=Path('large.py').read_text()
node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='chosen_value')
lines=text.splitlines(keepends=True)
assert hashlib.sha256(''.join(lines[:node.lineno-1]).encode()).hexdigest()==PREFIX
assert hashlib.sha256(''.join(lines[node.end_lineno:]).encode()).hexdigest()==SUFFIX
assert hashlib.sha256(Path('consumer.py').read_bytes()).hexdigest()==CONSUMER
print('window-contract-ok')
'''.replace('PREFIX',repr(hashlib.sha256(prefix.encode()).hexdigest())).replace('SUFFIX',repr(hashlib.sha256(suffix.encode()).hexdigest())).replace('CONSUMER',repr(hashlib.sha256(consumer.encode()).hexdigest()))
gate=ProcessGate(cases=(ProcessCase(command=('python','-c',check),expected_stdout='window-contract-ok\n'),))
fixture=json.loads(Path('.scratch/local-lights-out-factory/leds-modes-fixture.json').read_text());profile=ModelProfile.model_validate_json(json.dumps(fixture['policy']['model_profile'])).model_copy(update={'profile_id':'vllm-python-worker-windows-v1'})
fields=json.loads(Path('examples/work-atom.json').read_text());fields.update(atom_id='window-large-v2',objective='In large.py extend chosen_value(value=42) to clamp built-in integers to 0..100 inclusive. With no argument return 42. Reject booleans and every non-built-in-integer input with TypeError. Preserve all other source text exactly. consumer.render is a read-only caller and must work unchanged.',requirement_ids=['clamp'],writable_paths=['large.py'],prohibited_paths=[],required_gates=[{'gate_id':'behavior-preservation','validator_digest':gate.digest()}],max_attempts=2,context_budget={'total_tokens':12288,'output_tokens':4096});fields['inputs_digest']=InputSnapshot(source_digest=source.digest(),source_revision=fields['source_revision']).digest();atom=WorkAtom.model_validate_json(json.dumps(fields))
plan=RunPlan(atom=atom,source=source,gates={'behavior-preservation':gate},model_profile=profile,deployment=fixture['policy']['deployment'],broker_image=fixture['request']['environments']['python']['image'],selected_paths=('large.py','consumer.py'))
(root/'plan.json').write_text(plan.canonical()+'\n')
with WorkLedger(root/'ledger.db') as ledger:
 prepare_run(ledger,plan);result=Controller(ledger,LocalModel(ledger.artifacts,profile),DockerBroker(ledger.artifacts,plan.broker_image)).run(atom.atom_id)
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)
