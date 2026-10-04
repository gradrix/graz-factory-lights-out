"""Owned rig post-trial API controls; no model access."""
import hashlib,io,json,os,pathlib,subprocess,sys,time
sys.path.insert(0,'/home/gradrix/gflo-planning-d186b93')
os.environ['PYTHONPATH']='/home/gradrix/gflo-planning-d186b93'
from gflo.environment import resolve_binding
from gflo.guard import run
root=pathlib.Path(__file__).resolve().parent
binding=json.loads((root/'environment-bindings.json').read_bytes())['python-api']
environment=resolve_binding(binding)
assert environment.image=='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
results=root/'results-docs';results.mkdir()
def hashes(path):
 return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob('*')) if p.is_file() and not p.is_symlink()}
projects=[(n,root/'controls'/n)for n in ['conforming','scalar-depth-mutant','missing-body-mutant','validation-order-mutant']]
projects += [('arm3',pathlib.Path('/home/gradrix/gflo-planning-d186b93/trial-1/3-config-preview-decomposed/factory/300151e5e413/workspace')),('arm4',pathlib.Path('/home/gradrix/gflo-planning-d186b93/trial-1/4-config-preview-direct/factory/a8aac6d4726e/workspace'))]
projects=[(n,p) for n,p in projects if n in ('conforming','arm3','arm4')]
all_results=[]
for label,project in projects:
 before=hashes(project);name='gflo-api-docqa-1-'+label
 args=['docker','run','--rm','--pull','never','--name',name,'--runtime','runc','--network','none','--log-driver','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--memory-swap','1g','--cpus','2','--pids-limit','128','--shm-size','16m','--user',f'{os.getuid()}:{os.getgid()}','--init','--tmpfs','/tmp:rw,nosuid,nodev,size=192m','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/opt/deps','--workdir','/tmp','--mount',f'type=bind,src={project},dst=/workspace,readonly','--mount',f'type=bind,src={environment.dependencies},dst=/opt/deps,readonly','--mount',f'type=bind,src={root/"qa-api-doc-command.py"},dst=/qa-api-probes.py,readonly',environment.image,'python','-B','/qa-api-probes.py','--project','/workspace']
 output=io.BytesIO();receipt=results/(label+'-creation.json')
 facts={'label':label,'source_hashes':before,'command':args}
 try:
  facts['execution']=run(args,name,90,output=output,max_output_bytes=2*1024*1024,inspect_path=receipt)
 finally:
  (results/(label+'.stdout')).write_bytes(output.getvalue())
  removed=subprocess.run(['docker','rm','-f',name],capture_output=True,text=True,timeout=15)
  query=subprocess.run(['docker','ps','-aq','--filter','name=^/'+name+'$'],capture_output=True,text=True,timeout=10,check=True)
  facts['absence_confirmed']=not query.stdout.strip()
  facts['source_unchanged']=hashes(project)==before
  facts['creation_attested']=receipt.is_file()
  (results/(label+'-execution.json')).write_text(json.dumps(facts,indent=2)+'\n')
  all_results.append(facts)
  (results/'results.json').write_text(json.dumps(all_results,indent=2)+'\n')
 if not facts['absence_confirmed'] or not facts['source_unchanged'] or not facts['creation_attested']:raise RuntimeError('Post-QA integrity or lifetime uncertainty')
 print(label,facts['execution']['exit_code'],round(facts['execution']['elapsed_s'],3),flush=True)
