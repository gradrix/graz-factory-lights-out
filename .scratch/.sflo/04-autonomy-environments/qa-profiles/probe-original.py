import contextlib,io,json,pathlib,sys,tempfile,subprocess,traceback
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'03-autonomy-review'))
from qa_pinned import activate
activate('51479e9663f810e33031774abceca067cd761a48')
from gflo.__main__ import main
from gflo.environment import EnvironmentStore,runtime_context
from gflo.prepare import infer_profile,validate_project
from gflo.runner import Factory
from gflo.sandbox import Sandbox
OUT=pathlib.Path(__file__).resolve().parent;ROOT=pathlib.Path(tempfile.mkdtemp(prefix='gflo-profiles-qa-'));REF=pathlib.Path('.gflo/environment-coding-qualification-v2').resolve();rows=[]
def save(): (OUT/'results.json').write_text(json.dumps({'candidate':'51479e9663f810e33031774abceca067cd761a48','root':str(ROOT),'results':rows},indent=2)+'\n')
for profile in ['python-stdlib','python-api','node-ts']:
 row={'profile':profile};rows.append(row);save()
 try:
  project=ROOT/profile/'repo';project.mkdir(parents=True)
  for name,content in json.loads((REF/'private'/f'{profile}-reference.json').read_text()).items():
   p=project/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
  for cmd in [['git','init','-q',str(project)],['git','-C',str(project),'add','.'],['git','-C',str(project),'-c','user.name=QA','-c','user.email=qa@local','commit','-qm','reference']]:subprocess.run(cmd,check=True)
  store=ROOT/profile/'store';args=['--config','/nonexistent/config','environment','--store',str(store)]
  assert not store.exists();assert infer_profile(project)==profile
  with contextlib.redirect_stdout(io.StringIO()) as output: code=main(args+['prepare',profile,'--project',str(project)])
  row['prepare_exit']=code;row['prepare_output']=output.getvalue();save();assert code==0
  env=EnvironmentStore(store).resolve(json.loads(output.getvalue())['id']);row['id']=env.id;row['runtime']=env.runtime
  with contextlib.redirect_stdout(io.StringIO()) as output:assert main(args+['inspect',env.id])==0
  (OUT/(profile+'-receipt.json')).write_text(output.getvalue())
  with contextlib.redirect_stdout(io.StringIO()) as output:assert main(args+['check',env.id,'--repeat','2'])==0
  (OUT/(profile+'-checks.json')).write_text(output.getvalue())
  sandbox=Sandbox('sha256:'+'0'*64);sandbox.bind(env)
  command=['node','/acceptance/check.cjs','/workspace'] if profile=='node-ts' else ['python','-B','/acceptance/check.py','/workspace']
  acceptance=REF/'tasks'/profile/'acceptance';row['scenarios']=[]
  for _ in range(2):
   result=sandbox.execute(project,command,acceptance=acceptance,timeout=120);row['scenarios'].append(result);save();assert result['exit_code']==0
  task=ROOT/profile/'task.json';task.write_text(json.dumps({'repo':str(project),'acceptance':str(acceptance),'objective':'Preserve conforming reference','checks':[command],'max_attempts':1}))
  calls=[]
  def worker(workspace,task,previous,attempt):calls.append(runtime_context(task));return {}
  state=ROOT/profile/'state';factory=Factory(state,worker,sandbox.verify,environment=env,bind_environment=sandbox.bind);rid=factory.create(task);factory.db.close()
  factory=Factory(state,worker,sandbox.verify,bind_environment=sandbox.bind);result=factory.resume(rid);row['run']=rid;row['status']=result['status'];save();assert result['status']=='accepted';assert profile in calls[0];assert factory.resume(rid)['status']=='accepted';row['restart_and_context']=True
  if profile!='python-stdlib':
   workspace=state/rid/'workspace';frozen=json.loads((state/rid/'task.json').read_text());name=next(iter(frozen['environment_inputs']));target=workspace/name;target.write_text(target.read_text()+'\n');assert not sandbox.verify(workspace,frozen)['passed'];row['manifest_tamper_rejected']=True
  row['passed']=True
 except Exception as exc:row['error']=repr(exc);row['traceback']=traceback.format_exc()
 save();print(profile,row.get('passed',False),row.get('error',''),flush=True)
assert all(row.get('passed') for row in rows)
