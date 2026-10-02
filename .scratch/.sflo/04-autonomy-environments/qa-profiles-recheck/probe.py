import hashlib,json,pathlib,sys,tempfile,shutil
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('25f75c3275739cc7cc2a4fc5a4e16580b81511d1')
from gflo.environment import EnvironmentStore,runtime_context,binding
from gflo.prepare import prepare
from gflo.sandbox import Sandbox
out=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(tempfile.mkdtemp(prefix='gflo-profiles-recheck-'));result={'candidate':'25f75c3275739cc7cc2a4fc5a4e16580b81511d1','root':str(root)}
def save():(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
# Real preparation failure in outer scratch cleanup, with empty and prior-good stores.
for existing in [False,True]:
 store=EnvironmentStore(root/str(existing));good=prepare(store,'python-stdlib') if existing else None
 before={p.relative_to(store.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob('*') if p.is_file() and not p.name.startswith('.')}
 from gflo.prepare import discard as real_discard
 def fail_work(path):
  if pathlib.Path(path).name.startswith('.work-'):raise OSError('QA outer cleanup failure')
  return real_discard(path)
 with patch('gflo.prepare.discard',side_effect=fail_work):
  try:prepare(store,'python-stdlib')
  except OSError as e:assert 'QA outer cleanup failure' in str(e)
  else:raise AssertionError('cleanup failure accepted')
 after={p.relative_to(store.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in store.root.rglob('*') if p.is_file() and not any(x.startswith('.') for x in p.relative_to(store.root).parts)}
 assert before==after,(before,after)
 if good:assert store.resolve(good.id).receipt_hash==good.receipt_hash
 else:assert not [p for p in store.root.iterdir() if not p.name.startswith('.')]
 result['cleanup_prior_good' if existing else 'cleanup_empty']='rejected; published content unchanged';save()
 for p in store.root.glob('.work-*'):real_discard(p)
# API src-layout imports must use the built wheel; acceptance independently passes.
prior=json.loads((out.parent/'qa-profiles/results.json').read_text());old=pathlib.Path(prior['root']);row=next(x for x in prior['results'] if x['profile']=='python-api');env=EnvironmentStore(old/'python-api/store').resolve(row['id']);workspace=root/'api';shutil.copytree(old/'python-api/repo',workspace)
(workspace/'tests').mkdir(exist_ok=True);test=workspace/'tests/test_installed.py';test.write_text('import unittest\nfrom reservation_preview.domain import preview\nclass Installed(unittest.TestCase):\n def test_installed(self):\n  self.assertEqual(preview({"a":2},[{"sku":"a","quantity":1}])["remaining"],{"a":1})\n')
acceptance=root/'acceptance';acceptance.mkdir();(acceptance/'check.py').write_text('print("independent acceptance control")\n')
sandbox=Sandbox();sandbox.bind(env);task={'checks':[['python','/acceptance/check.py']]};source_before=test.read_bytes();control=sandbox.verify(workspace,task,acceptance);result['api_control']=control;save();assert control['passed'] and len(control['checks'])==2;assert test.read_bytes()==source_before
# Genuine bad generated test must prevent acceptance even if external check passes.
test.write_text(source_before.decode().replace('{"a":1})','{"a":999})'));bad=sandbox.verify(workspace,task,acceptance);result['api_bad_generated_test']=bad;save();assert not bad['passed'] and bad['checks'][0]['exit_code']==0 and bad['checks'][1]['exit_code']!=0
assert 'Build your project wheel' in runtime_context({'environment':binding(env)})
result['passed']=True;save();print('PASS cleanup empty/prior-good and installed API generated-test control/negative')
