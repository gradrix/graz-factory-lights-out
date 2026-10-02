import subprocess,json,hashlib
from pathlib import Path
r=Path.cwd(); f=r/'.gflo/stage3-evidence/00cab7ec321d';o=r/'.scratch/.sflo/04-autonomy-environments/qa-model-node-failed'
c=['docker','run','--rm','--runtime=runc','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=128','--memory=512m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,exec,nosuid,size=256m']
for src,dst in [(f/'workspace','/source'),(f/'acceptance','/acceptance'),(r/'.gflo/environment-locks/node-ts/node_modules','/node_modules'),(o/'probe.cjs','/probe.cjs')]:c+=['-v',str(src)+':'+dst+':ro']
c+=['sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0','timeout','180','node','/probe.cjs']
p=subprocess.run(c,capture_output=True,text=True,timeout=190);d=dict(command=c,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,hashes={str(p.relative_to(f)):hashlib.sha256(p.read_bytes()).hexdigest() for p in f.rglob('*') if p.is_file() and 'snapshot.git' not in str(p)})
(o/'receipt.json').write_text(json.dumps(d,indent=2)+'\n');print(p.returncode,p.stderr,p.stdout[-1000:])
