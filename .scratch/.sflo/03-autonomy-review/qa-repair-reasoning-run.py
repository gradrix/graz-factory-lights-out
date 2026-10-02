from pathlib import Path
import json,subprocess,base64,hashlib,difflib
root=Path.cwd();out=root/'.scratch/.sflo/03-autonomy-review/repair-reasoning-evidence';out.mkdir(exist_ok=True);private=root/'.gflo/semantic-repair-reasoning';private.mkdir(exist_ok=True)
remote='''from pathlib import Path
import json,base64
root=Path('/home/gradrix/gflo-runtime/.gflo/repair-reasoning-paired-v1');d=json.loads((root/'receipt.json').read_text());out=[]
for a in d['arms']:
 run=root/a['label']/'state'/a['run_id'];files={}
 for p in [run/'task.json',*run.glob('workspace/**/*.py'),*run.glob('workspace/**/README.md'),*run.glob('acceptance/*.py'),*run.glob('attempts/*/verification.json'),*run.glob('attempts/*/review.json')]:
  if p.is_file() and not p.is_symlink():files[str(p.relative_to(run))]=base64.b64encode(p.read_bytes()).decode()
 out.append({'label':a['label'],'files':files})
print(json.dumps(out))
'''
records=json.loads(subprocess.check_output(['ssh','monster-gaming-pc.lan','python3','-'],input=remote,text=True));paired=json.loads((root/'.scratch/.sflo/03-autonomy-review/repair-reasoning-paired.json').read_text())
for r in records:
 label=r['label'];dest=private/label;dest.mkdir(exist_ok=True)
 for name,data in r['files'].items():p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
 arm=next(a for a in paired['arms'] if a['label']==label);baseline=root/'.gflo/semantic-c'/arm['source_run_id']/'workspace';patch=[]
 for name in sorted(n for n in r['files'] if n.startswith('workspace/')):
  rel=name[10:];p=baseline/rel;patch.extend(difflib.unified_diff(p.read_text().splitlines(True) if p.exists() else [],(dest/name).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
 (out/(label+'.patch')).write_text(''.join(patch))
 hashes={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in r['files']}
 base=['docker','run','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,noexec,nosuid,size=16m','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(dest/'workspace')+':/workspace:ro','-v',str(dest/'acceptance')+':/acceptance:ro','-w','/workspace',paired['image'],'timeout','35']
 checks=[]
 for args in [['python','-B','-I','/acceptance/check.py'],['python','-B','-m','unittest','discover','-v']]:
  p=subprocess.run(base+args,capture_output=True,text=True,timeout=40);checks.append(dict(command=base+args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
 receipt=dict(label=label,run=arm['run_id'],raw_status=arm['status'],hashes=hashes,checks=checks)
 (out/(label+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 for p in (dest/'attempts').glob('*/*.json'):(out/(label+'-'+p.name)).write_bytes(p.read_bytes())
 print(label,[c['exit'] for c in checks])
