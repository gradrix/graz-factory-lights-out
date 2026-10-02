from pathlib import Path
import json,subprocess,hashlib
root=Path.cwd();frozen=root/'.gflo/stage3-evidence/d535632d4d5f';out=root/'.scratch/.sflo/04-autonomy-environments/qa-model-stdlib';image='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
base=['docker','run','--runtime=runc','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,noexec,nosuid,size=16m','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(frozen/'workspace')+':/project with spaces:ro','-v',str(frozen/'acceptance')+':/acceptance:ro','-v',str(out/'probe.py')+':/probe.py:ro','-w','/project with spaces',image,'timeout','35']
checks=[]
for name,args in [('oracle',['python','-B','/acceptance/check.py','.']),('documented-tests',['python','-B','-m','unittest','discover','-s','tests']),('supplemental',['python','-B','/probe.py']),('runtime',['python','-c','import sys;print(sys.version);assert sys.version_info[:3]==(3,12,13)'])]:
 c=base+args;p=subprocess.run(c,capture_output=True,text=True,timeout=40);checks.append(dict(name=name,command=c,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));print(name,p.returncode,p.stdout,p.stderr[-300:])
hashes={str(p.relative_to(frozen)):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen.rglob('*') if p.is_file()}
(out/'receipt.json').write_text(json.dumps(dict(checks=checks,hashes=hashes),indent=2)+'\n')
