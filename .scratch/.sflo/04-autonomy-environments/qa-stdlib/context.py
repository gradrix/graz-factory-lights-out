import json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('841dad8c7341f2212562771b2e9ece0e215a0b9c')
from gflo.environment import EnvironmentStore,runtime_context
from gflo.observe import Observer
from gflo.worker import ModelWorker
from gflo.review import Reviewer
from gflo.sandbox import Sandbox
out=pathlib.Path(__file__).resolve().parent;prior=json.loads((out/'result.json').read_text());root=pathlib.Path(prior['root']);view=Observer(root/'state');observed=view.status(prior['run']);print('tampered observer status',observed['status'])
try:EnvironmentStore(root/'store').resolve(prior['environment'])
except ValueError:pass
else:raise AssertionError('tamper control did not reject')
(root/'store'/prior['environment']/'deps').chmod(0o555)
env=EnvironmentStore(root/'store').resolve(prior['environment']);sandbox=Sandbox('sha256:'+'0'*64);sandbox.bind(env)
workspace=root/'state'/prior['run']/'workspace';facts=sandbox.execute(workspace,['python','-c',"import glob,json,pathlib,platform;print(json.dumps({'python':platform.python_version(),'gpu':glob.glob('/dev/nvidia*')+glob.glob('/dev/dri*'),'limits':{p:pathlib.Path('/sys/fs/cgroup/'+p).read_text().strip() for p in ['memory.max','memory.swap.max','pids.max','cpu.max']}}))"]);assert facts['exit_code']==0;actual=json.loads(facts['output']);assert actual['gpu']==[] and actual['python']=='3.12.13';assert actual['limits']['memory.max']=='1073741824' and actual['limits']['pids.max']=='128'
task=json.loads((workspace.parent/'task.json').read_text());worker=ModelWorker({'endpoint':'http://127.0.0.1:1','model':'mock','reasoning':'medium'},sandbox);requests=[]
def response(path,body,**kwargs):requests.append(body);return {'choices':[{'message':{'role':'assistant','content':'Done'}}]}
worker.request=response;worker(workspace,task,None,99);assert runtime_context(task) in requests[-1]['messages'][1]['content']
def reviewresponse(path,body,**kwargs):requests.append(body);return {'choices':[{'message':{'role':'assistant','content':json.dumps({'decision':'pass','findings':[],'question':''})}}]}
worker.request=reviewresponse;assert Reviewer(worker)(workspace,task)['decision']=='pass';assert '3.12.13' in requests[-1]['messages'][1]['content'] and 'python-stdlib' in requests[-1]['messages'][1]['content'];assert 'legacy-unbound' in runtime_context({})
(out/'context-result.json').write_text(json.dumps({'observer_tampered_status':observed['status'],'actual':actual,'worker_context':True,'reviewer_context':True,'legacy_context_explicit':True},indent=2)+'\n');print('PASS runtime/resources/noGPU/context/legacy markers; tampered Observer accepted reproduced')
