import dataclasses,hashlib,json,os,pathlib,shutil,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'private/control-results';assert not OUT.exists();OUT.mkdir();sys.path.insert(0,'/home/gradrix/gflo-documents-92deaab')
from gflo.environment import EnvironmentStore
STORE=pathlib.Path('/home/gradrix/gflo-stage3-25f75c3/.gflo/stage3-preparation/environments');ids={'python-stdlib':'36cd138cbdc332246a2db473301200117f82404a4504c675db95966645348975','python-api':'e591c2d6f97b02fc2a99ecef01848a4e74d743e499aeec3b4d4d7d6c6c400acb'};bindings={};rows=[]
def save(): (OUT/'results.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n')
for profile,identifier in ids.items():
 env=EnvironmentStore(STORE).resolve(identifier,identifier);assert env.profile==profile and env.runtime['python']=='3.12.13';bindings[profile]={k:str(v) if isinstance(v,pathlib.Path)else v for k,v in dataclasses.asdict(env).items()}
def run(case,source,phase,label,expected):
 profile='python-api' if case=='config-preview'else 'python-stdlib';binding=bindings[profile];name='gflo-fixture-'+uuid.uuid4().hex[:12];start=time.monotonic();args=['docker','create','--pull','never','--name',name,'--runtime','runc','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--memory-swap','1g','--cpus','2','--pids-limit','128','--user',f'{os.getuid()}:{os.getgid()}','--init','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/opt/deps','--workdir','/workspace']
 for src,dst in [(source,'/workspace'),(ROOT/'cases'/case/'acceptance','/acceptance'),(pathlib.Path(binding['dependencies']),'/opt/deps')]:args+=['--mount',f'type=bind,src={src},dst={dst},readonly']
 args +=[binding['image'],'python','-I','/acceptance/check.py','--project','/workspace','--phase',phase]
 try:
  subprocess.run(args,capture_output=True,check=True,timeout=20);facts=json.loads(subprocess.check_output(['docker','inspect',name],timeout=10))[0];(OUT/(label+'-container.json')).write_text(json.dumps({'image':facts['Image'],'host':facts['HostConfig'],'mounts':facts['Mounts'],'config':{k:facts['Config'][k]for k in ['User','Cmd','Env']}},indent=2));assert facts['Image']==binding['image'];r=subprocess.run(['docker','start','-a',name],capture_output=True,text=True,timeout=90);(OUT/(label+'.log')).write_text(r.stdout+r.stderr);row={'case':case,'label':label,'phase':phase,'expected_pass':expected,'exit':r.returncode,'elapsed_s':time.monotonic()-start,'matched':(r.returncode==0)==expected};rows.append(row);save()
 finally:
  subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=30);assert not subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+name+'$'],text=True,timeout=10).strip()
for case in (sys.argv[1:] or ['manifest-reconcile','config-preview']):
 for role in ['starter','reference']:
  source=ROOT/'cases'/case/'source' if role=='starter'else ROOT/'private/references'/case
  for phase in ['milestone','full']:run(case,source,phase,case+'-'+role+'-'+phase,role=='reference')
# Independent negative controls on disposable reference copies.
variants=[('manifest-reconcile','bool-size','manifest_tool/validation.py','type(size)is not int','not isinstance(size,int)'),('manifest-reconcile','greedy-rename','manifest_tool/domain.py','if len(old)==len(new)==1:','if old and new:'),('config-preview','bool-test','src/config_preview/domain.py','if type(a)is not type(b):return False','if False:return False'),('config-preview','mutates-input','src/config_preview/domain.py','result=copy.deepcopy(base)','result=base')]
for case,label,file,old,new in variants:
 if sys.argv[1:] and case not in sys.argv[1:]:continue
 source=ROOT/'private/control-candidates'/label;shutil.copytree(ROOT/'private/references'/case,source);p=source/file;s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new));run(case,source,'full',label,False)
for case in (sys.argv[1:] or ['manifest-reconcile','config-preview']):
 for label in ['missing-tests','unchanged-docs']:
  source=ROOT/'private/control-candidates'/(case+'-'+label);shutil.copytree(ROOT/'private/references'/case,source)
  if label=='missing-tests':shutil.rmtree(source/'tests')
  else:shutil.copyfile(ROOT/'cases'/case/'source/README.md',source/'README.md')
  run(case,source,'full',case+'-'+label,False)
for profile,identifier in ids.items():assert EnvironmentStore(STORE).resolve(identifier,identifier).receipt_hash==identifier
save();assert all(r['matched']for r in rows),rows;print('PASS',len(rows),'expected starter/reference/mutant/quality controls')
