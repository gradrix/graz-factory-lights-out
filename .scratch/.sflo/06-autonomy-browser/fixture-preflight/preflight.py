import subprocess,pathlib,json,os,uuid
r=pathlib.Path.cwd();name='gflo-browser-fixture-'+uuid.uuid4().hex[:10];cmd=['docker','run','--rm','--pull','never','--runtime','runc','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','128m','--memory-swap','128m','--cpus','0.25','--pids-limit','64','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,nosuid,nodev,size=16m,mode=1777','--mount',f'type=bind,src={r}/evaluations/local-browser,dst=/fixture,readonly','--mount',f'type=bind,src={r}/.gflo/browser-qualification/http-preflight.cjs,dst=/probe.cjs,readonly','sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0','node','/probe.cjs']
try:p=subprocess.run(cmd,text=True,capture_output=True,timeout=90)
finally:subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
(r/'.gflo/browser-qualification/http-results.json').write_text(json.dumps({'command':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n');print(p.returncode,p.stdout[-1000:],p.stderr);assert p.returncode==0
for path in (r/'evaluations/local-browser').rglob('*.cjs'):subprocess.run(['node','--check',str(path)],check=True)
print('PASS syntax all cjs')
