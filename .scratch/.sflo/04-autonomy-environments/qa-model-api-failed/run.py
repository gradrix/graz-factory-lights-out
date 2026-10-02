from pathlib import Path
import subprocess,json,hashlib
root=Path.cwd();out=root/'.scratch/.sflo/04-autonomy-environments/qa-model-api-failed';frozen=root/'.gflo/stage3-evidence/70a187241924';image='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
c=['docker','run','--runtime=runc','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=128','--memory=512m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,exec,nosuid,size=512m','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(frozen/'workspace')+':/project with spaces:ro','-v',str(frozen/'acceptance')+':/acceptance:ro','-v',str(root/'.gflo/environment-locks/python-api/wheels')+':/wheels:ro','-v',str(out/'probe.py')+':/probe.py:ro',image,'timeout','180','python','-B','/probe.py']
p=subprocess.run(c,capture_output=True,text=True,timeout=190);receipt=dict(command=c,exit=p.returncode,stderr=p.stderr)
if p.returncode==0:receipt['checks']=json.loads(p.stdout.splitlines()[-1])
else:receipt['stdout']=p.stdout
receipt['hashes']={str(p.relative_to(frozen)):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen.rglob('*') if p.is_file()}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('exit',p.returncode,p.stderr[-1500:]);print([(x['label'],x['exit']) for x in receipt.get('checks',[])])
