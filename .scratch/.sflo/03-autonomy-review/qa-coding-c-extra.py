from pathlib import Path
import subprocess,json
root=Path.cwd();pub=root/'.scratch/.sflo/03-autonomy-review/coding-c-evidence'
for p in (root/'.gflo/semantic-c').glob('*/audit.json'):
 a=json.loads(p.read_text());task=a['task'];dest=pub/(task+'-extra.json')
 if dest.exists() or (a['status']=='accepted' and task[:2] not in ('01','08','12')):continue
 work=p.parent/'workspace';fixture=root/'evaluations/coding-c/tasks'/task
 if not fixture.exists():continue
 base=['docker','run','--rm','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs=/tmp:rw,noexec,nosuid,size=16m','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(work)+':/workspace:ro','-v',str(fixture/'acceptance')+':/acceptance:ro','-v',str(pub/'supplemental-probe.py')+':/probe.py:ro','-w','/workspace',a['image']]
 commands=[['python','-B','/probe.py',task[:2]]] if a['status']=='accepted' else [['python','-B','-I','/acceptance/check.py'],['python','-B','-m','unittest','discover','-v'],['python','-B','-m','unittest','discover','-s','tests','-v']]
 if a['status']!='accepted' and task[:2]=='08':commands.append(['python','-B','/probe.py','08'])
 receipts=[]
 for args in commands:
  c=base+['timeout','35']+args;p2=subprocess.run(c,capture_output=True,text=True,timeout=40);receipts.append(dict(command=c,exit=p2.returncode,stdout=p2.stdout,stderr=p2.stderr))
 dest.write_text(json.dumps(receipts,indent=2)+'\n'); print(task,[(r['exit'],r['stderr'][-150:]) for r in receipts])
