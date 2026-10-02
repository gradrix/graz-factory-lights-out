import json,pathlib,sys,shutil,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('51479e9663f810e33031774abceca067cd761a48')
from gflo.environment import EnvironmentStore,runtime_context
from gflo.prepare import validate_project,infer_profile
from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker
from gflo.review import Reviewer
out=pathlib.Path(__file__).resolve().parent;prior=json.loads((out/'results.json').read_text());root=pathlib.Path(prior['root']);rows=[]
for row in prior['results']:
 profile=row['profile'];env=EnvironmentStore(root/profile/'store').resolve(row['id']);sandbox=Sandbox();sandbox.bind(env);state=root/profile/'state'/row['run'];workspace=state/'workspace';task=json.loads((state/'task.json').read_text());result={'profile':profile}
 if profile!='python-stdlib':
  for name,digest in task['environment_inputs'].items():shutil.copyfile(root/profile/'repo'/name,workspace/name)
  assert sandbox.verify(workspace,task,state/'acceptance')['passed']
  name=next(iter(task['environment_inputs']));target=workspace/name;target.write_text(target.read_text()+'\n');assert not sandbox.verify(workspace,task,state/'acceptance')['passed'];shutil.copyfile(root/profile/'repo'/name,target);result['manifest_tamper_rejected']=True
 worker=ModelWorker({'endpoint':'http://127.0.0.1:1','model':'mock','reasoning':'medium'},sandbox);requests=[]
 def response(path,body,**kwargs):requests.append(body);return {'choices':[{'message':{'role':'assistant','content':'Done'}}]}
 worker.request=response;worker(workspace,task,None,99);assert runtime_context(task) in requests[-1]['messages'][1]['content']
 def response(path,body,**kwargs):requests.append(body);return {'choices':[{'message':{'role':'assistant','content':json.dumps({'decision':'pass','findings':[],'question':''})}}]}
 worker.request=response;assert Reviewer(worker)(workspace,task)['decision']=='pass';assert profile in requests[-1]['messages'][1]['content'];result['worker_reviewer_context']=True
 if profile!='python-stdlib':
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);shutil.copytree(root/profile/'repo',p/'repo');p=p/'repo'
   target=p/('package-lock.json' if profile=='node-ts' else 'pyproject.toml');original=target.read_text()
   for label,content in [('malformed','{broken'),('unsupported',original.replace('5.8.3','9.9.9') if profile=='node-ts' else original.replace('0.115.12','9.9.9'))]:
    target.write_text(content)
    try:validate_project(EnvironmentStore(root/profile/'store'),profile,p)
    except ValueError as e:result[label]=str(e)[-300:]
    else:raise AssertionError(label+' accepted')
   target.unlink()
   try:validate_project(EnvironmentStore(root/profile/'store'),profile,p)
   except ValueError:result['missing_rejected']=True
   else:raise AssertionError('missing accepted')
 rows.append(result);(out/'boundaries-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(profile,'PASS',flush=True)
