from pathlib import Path
import subprocess,json,base64,hashlib,difflib
root=Path.cwd(); private=root/'.gflo/semantic-d';public=root/'.scratch/.sflo/03-autonomy-review/coding-d-evidence';private.mkdir(exist_ok=True);public.mkdir(exist_ok=True)
remote='''from pathlib import Path
import sqlite3,json,base64
root=Path('/home/gradrix/gflo-runtime/.gflo/stage2-coding-d')
c=sqlite3.connect('file:'+str(root/'state.sqlite')+'?mode=ro',uri=True)
rows=c.execute('select id,status,attempts,contract_hash from runs').fetchall()
out=[]
for run,status,attempts,contract in rows:
 item={'run':run,'status':status,'attempts':attempts,'contract':contract,'files':{}}
 if status not in ('running','pending','queued'):
  p=root/run
  paths=[p/'task.json',*p.glob('workspace/**/*.py'),*p.glob('workspace/**/README.md'),*p.glob('acceptance/*.py'),*p.glob('attempts/*/verification.json'),*p.glob('attempts/*/review.json'),*p.glob('attempts/*/project-tests.json'),*p.glob('attempts/*/question-assessment.json')]
  for f in paths:
   if f.is_file() and not f.is_symlink() and f.stat().st_size<1000000:item['files'][str(f.relative_to(p))]=base64.b64encode(f.read_bytes()).decode()
 out.append(item)
print(json.dumps(out))
'''
rows=json.loads(subprocess.check_output(['ssh','monster-gaming-pc.lan','python3','-'],input=remote,text=True))
image=subprocess.check_output(['docker','image','inspect','python:3.12-slim','--format','{{.Id}}'],text=True).strip()
for row in rows:
 run=row['run']; files=row.pop('files'); dest=private/run
 if not files or (dest/'audit.json').exists():continue
 dest.mkdir(exist_ok=True)
 for name,data in files.items():
  p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
 hashes={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in files};row['hashes']=hashes
 task=json.loads((dest/'task.json').read_text()); fixtures=list((root/'evaluations/coding-d/tasks').glob('*/task.json'))+[root/'evaluations/coding-d/ambiguous/task.json'];fixture=next(p.parent for p in fixtures if json.loads(p.read_text())['objective']==task['objective']);row['task']=fixture.name
 checks=[]
 if row['status']=='accepted':
  base=['docker','run','--runtime=runc','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,noexec,nosuid,size=16m','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(dest/'workspace')+':/workspace:ro','-v',str(fixture/'acceptance')+':/acceptance:ro','-w','/workspace',image]
  for name,args in [('acceptance',['python','-B','-I','/acceptance/check.py']),('generated',['python','-B','-m','unittest','discover','-v'])]:
   try:
    p=subprocess.run(base+['timeout','35']+args,capture_output=True,text=True,timeout=40);checks.append({'name':name,'command':base+['timeout','35']+args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
   except subprocess.TimeoutExpired:checks.append({'name':name,'timeout':True})
 row.update(checks=checks,image=image)
 (dest/'audit.json').write_text(json.dumps(row,indent=2)+'\n');(public/(fixture.name+'-receipt.json')).write_text(json.dumps(row,indent=2)+'\n')
 patch=[]
 for name in sorted(n for n in files if n.startswith('workspace/')):
  relative=name[len('workspace/'):]; original=fixture/'source'/relative
  patch.extend(difflib.unified_diff(original.read_text().splitlines(True) if original.exists() else [],(dest/name).read_text().splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
 (public/(fixture.name+'.patch')).write_text(''.join(patch))
 print('CAPTURED',fixture.name,run,row['status'],[(x['name'],x.get('exit','timeout')) for x in checks])
print('STATUS',[(r['run'],r['status']) for r in rows])
