import hashlib,json,os,pathlib,subprocess,time,uuid
root=pathlib.Path('/home/gradrix/gflo-planning-postqa-manifest-1');image='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc';trial=pathlib.Path('/home/gradrix/gflo-planning-d186b93/trial-1');sources=[trial/'1-manifest-reconcile-direct/factory/b420f7770b76/workspace',trial/'2-manifest-reconcile-decomposed/factory/037a513a8192/workspace']
def hashes(p):return {str(f.relative_to(p)):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'mode':f.stat().st_mode&511}for f in sorted(p.rglob('*'))if f.is_file()}
before=[hashes(p)for p in sources];rows=[]
for arm,source in enumerate(sources,1):
 control=root/f'control{arm}';subprocess.run(['python3',str(root/'qa-manifest-controls.py'),'--arm',str(arm),'--source',str(source),'--output',str(control)],check=True)
 for role,candidate in [('original',source),('control',control)]:
  label=f'arm{arm}-{role}';name='gflo-postqa-'+uuid.uuid4().hex[:12];start=time.monotonic()
  args=['docker','create','--pull','never','--runtime','runc','--name',name,'--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','512m','--memory-swap','512m','--cpus','1','--pids-limit','64','--init','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--env','PYTHONDONTWRITEBYTECODE=1','--workdir','/candidate','--mount',f'type=bind,src={candidate},dst=/candidate,readonly','--mount',f'type=bind,src={root},dst=/probe,readonly',image,'python','/probe/qa-manifest-probes.py','--arm',str(arm)]
  try:
   created=subprocess.check_output(args,text=True).strip();facts=json.loads(subprocess.check_output(['docker','inspect',created]))[0];assert facts['Image']==image;(root/(label+'-container.json')).write_text(json.dumps(facts,indent=2));result=subprocess.run(['docker','start','-a',created],capture_output=True,text=True,timeout=60);(root/(label+'.json')).write_text(result.stdout);(root/(label+'.stderr')).write_text(result.stderr);data=json.loads(result.stdout);rows.append({'arm':arm,'role':role,'exit':result.returncode,'elapsed_s':time.monotonic()-start,'checks':data['rows']})
  finally:
   subprocess.run(['docker','rm','-f',name],capture_output=True,check=True);assert not subprocess.check_output(['docker','ps','-aq','--filter','name=^/'+name+'$'],text=True).strip()
assert [hashes(p)for p in sources]==before
(root/'results.json').write_text(json.dumps({'rows':rows,'originals_unchanged':True,'source_hashes':before,'image':image,'cleanup_confirmed':True},indent=2));print(json.dumps([{'arm':r['arm'],'role':r['role'],'exit':r['exit'],'checks':[(x['name'],x['passed'])for x in r['checks']]}for r in rows],indent=2))
