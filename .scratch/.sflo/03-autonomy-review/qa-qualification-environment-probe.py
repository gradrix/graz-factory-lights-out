import json,pathlib,tempfile,unittest.mock as mock
from qa_pinned import activate
activate('4a552b6418220c92b33e5b1f22655293b3354702')
import ops.qualify_coding as q
from gflo.sandbox import Sandbox
base=pathlib.Path(__file__).resolve().parent;repo=base.parents[2];manifest=json.loads((repo/'.gflo/coding-qualification-d/manifest.json').read_text());expected=manifest['environment'];results=[]
r=q.environment_check(Sandbox(expected['image']),expected);assert r['passed'] and r['observed']['version']=='3.12.13';results.append(dict(case='actual-D-environment',result=r))
for image,environment in [(expected['image'],dict(expected,version='0.0.0')),('sha256:'+'0'*64,expected)]:
 with tempfile.TemporaryDirectory() as temp:
  root=pathlib.Path(temp);fixtures=root/'fixtures';fixtures.mkdir();(fixtures/'manifest.json').write_text(json.dumps({'sha256':{},'environment':environment}));config=root/'config.json';config.write_text(json.dumps({'image':image}));state=root/'state'
  with mock.patch('sys.argv',['qualify',str(fixtures),str(state),'--config',str(config)]),mock.patch.object(q,'ModelWorker') as model,mock.patch.object(q,'Factory') as factory:
   assert q.main()==2;model.assert_not_called();factory.assert_not_called()
  receipt=json.loads((state/'environment.json').read_text());assert receipt['passed'] is False;assert not (state/'state.sqlite').exists();results.append(dict(case='missing-image' if image.endswith('0'*64) else 'version-mismatch',result=receipt))
for output in ['invalid JSON','[]','{"version":"3.12.13","implementation":"CPython"}']:
 sandbox=mock.Mock();sandbox.execute.return_value={'image':expected['image'],'exit_code':0,'output':output}
 r=q.environment_check(sandbox,expected);assert r['passed'] is False and 'invalid runtime facts' in r['error'];results.append(dict(case='malformed-runtime',result=r))
# Legacy cohorts retain observed facts even without an expected target.
r=q.environment_check(Sandbox(expected['image']));assert r['passed'] and r['expected'] is None and r['observed']['version']=='3.12.13';results.append(dict(case='legacy-observed-facts',result=r))
(base/'qa-qualification-environment-probe.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS actual D target, mismatch-before-model, missing-image-before-model, malformed runtime fail closed, legacy facts; no model calls')
