import json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('25f75c3275739cc7cc2a4fc5a4e16580b81511d1')
from gflo.environment import EnvironmentStore
from gflo.prepare import prepare
out=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(json.loads((out/'results.json').read_text())['root']);store=EnvironmentStore(root/'sigkill');assert list(store.root.glob('.work-*'));env=prepare(store,'python-stdlib');assert not list(store.root.glob('.work-*'));assert store.resolve(env.id).receipt_hash==env.receipt_hash
(out/'recovery-result.json').write_text(json.dumps({'candidate':'25f75c3275739cc7cc2a4fc5a4e16580b81511d1','environment':env.id,'stale_scratch_removed':True,'fresh_preparation_passed':True},indent=2)+'\n');print('PASS recovery after SIGKILL')
