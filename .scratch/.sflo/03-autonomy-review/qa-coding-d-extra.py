from pathlib import Path
import json,subprocess
root=Path.cwd();pub=root/'.scratch/.sflo/03-autonomy-review/coding-d-evidence'
for f in sorted(pub.glob('*-receipt.json')):
 a=json.loads(f.read_text());kind=a['task'][:2];out=pub/(a['task']+'-supplemental.json')
 if a['status']!='accepted' or kind not in ('01','04','07','08','11') or out.exists():continue
 c=a['checks'][0]['command'];c.insert(2,'--runtime=runc') if '--runtime=runc' not in c else None;idx=c.index('-w');c[idx:idx]=['-v',str(pub/'supplemental-probe.py')+':/probe.py:ro'];idx=c.index('timeout');c=c[:idx]+['timeout','35','python','-B','/probe.py',kind]
 p=subprocess.run(c,capture_output=True,text=True,timeout=40);out.write_text(json.dumps(dict(command=c,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n');print(a['task'],p.returncode,p.stdout,p.stderr)
