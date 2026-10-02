import json,pathlib,hashlib,tempfile,subprocess,os,shutil,uuid
OUT=pathlib.Path(__file__).resolve().parent;R=pathlib.Path('.gflo/environment-node-followup').resolve();rows=[]
for path,digest in [(R,'2ec5da0ddb1c0e60996efa706360f397e3bc3433c45d05a70205ef48be4daf52'),(R.parent/'environment-node-followup-public','68292397b94126e485d7d119f6c2e6a5692d9232ea366665c309e79eb18d84b5')]:
 assert hashlib.sha256((path/'manifest.json').read_bytes()).hexdigest()==digest
 for name,h in json.loads((path/'manifest.json').read_text())['files'].items():assert hashlib.sha256((path/name).read_bytes()).hexdigest()==h
for kind in ['baseline','reference-extra','reverse-output']:
 with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d);root.chmod(0o755);source=root/'source';shutil.copytree(R/('tasks/node-ts/source' if kind=='baseline' else 'private/reference'),source);accept=root/'acceptance';accept.mkdir()
  if kind=='reverse-output':
   p=source/'src/domain.ts';s=p.read_text();assert 'return free;' in s;p.write_text(s.replace('return free;','return free.reverse();'))
  oracle=(R/'tasks/node-ts/acceptance/check.cjs').read_text()
  if kind=='reference-extra':
   extra="""
 good(payload({start:1,end:12},[{start:9,end:11},{start:3,end:8},{start:4,end:5},{start:3,end:8}],2),[{start:1,end:3,duration:2}]);
 bad(payload({start:10,end:20},[{start:-1,end:0}]));
 bad(payload({start:10,end:20},[{end:2}]));
 bad(payload({start:10,end:20},[{start:2,end:2.5}]));
 good(payload({start:0,end:1000000},[],1000000),[{start:0,end:1000000,duration:1000000}]);
"""
   oracle=oracle.replace(" good({action:'total'",extra+" good({action:'total'",1)
  (accept/'check.cjs').write_text(oracle);name='gflo-node-fixture-qa-'+uuid.uuid4().hex[:10]
  args=['docker','run','--rm','--pull','never','--runtime','runc','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--memory-swap','1g','--cpus','1','--pids-limit','128','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,nosuid,nodev,size=128m,mode=1777','--env','HOME=/tmp','--workdir','/tmp','--mount',f'type=bind,src={source},dst=/different project/source,readonly','--mount',f'type=bind,src={accept},dst=/acceptance,readonly','--mount',f'type=bind,src={R.parent}/environment-locks/node-ts/node_modules,dst=/node_modules,readonly','sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0','node','/acceptance/check.cjs','/different project/source']
  try:p=subprocess.run(args,capture_output=True,text=True,timeout=120)
  finally:subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
  rows.append({'case':kind,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(kind,p.returncode,flush=True)
assert [r['exit']==0 for r in rows]==[False,True,False]
