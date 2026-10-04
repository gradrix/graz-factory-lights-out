"""Admit and dispatch the single frozen four-case local-model discriminator."""
from pathlib import Path
import datetime,hashlib,json,shlex,subprocess
p=Path(__file__).resolve().parent
stage='/home/gradrix/gflo-review-37b7f1d';output=stage+'/trial-1'
command=['python3',stage+'/ops/executable_review_prototype.py','run',
 '--manifest',stage+'/evaluations/executable-review/manifest.json',
 '--manifest-sha256','05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37',
 '--config','/home/gradrix/gflo-runtime/.gflo/config.json',
 '--bindings',stage+'/inputs/environment-bindings.json','--identity',stage+'/inputs/expected-identity.json',
 '--output',output,'--lease','/home/gradrix/.local/state/gflo-planning-pilot/lease']
gates=['contract.md','builder-candidate.json','fixture-review.md','qa-harness.md','security.md','combined-controls.txt','staging.json']
admission={'status':'admitted once by root under existing user authorization','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'prototype_commit':'37b7f1d1416d5497ca38291b47b364882d2d44ef','mechanism_sha256':'ede30d388c75b1c69c683dbd4c61cae408afc73cd5d35f84c1748d0ab281ecaa',
 'contract_sha256':'1fe3c4763dd4e1ee6d3b280619dcbce4ac1814d7253dbbba5c1d8d6f47f959d1',
 'inventory_sha256':'c9ce412c03798dcbb4c68502bc0e5ab5ea9c19f3ba031d2874b5046fc0827aac',
 'gates_sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest()for name in gates},
 'limits_per_case':{'requests':8,'commands':12,'work_s':300,'cleanup_s':150},
 'order':['case-01','case-02','case-03','case-04'],'command':command,
 'scope':'Known defect/control reviews only. No candidate repairs, human hints, retries, maintained promotion or serving changes.'}
assert not(p/'trial-1-admission.json').exists()
raw=json.dumps(admission,indent=2).encode()+b'\n';(p/'trial-1-admission.json').write_bytes(raw)
remote='''import hashlib,json,os,pathlib,stat,subprocess,sys,datetime
stage=pathlib.Path(STAGE);raw=sys.stdin.buffer.read();a=json.loads(raw)
assert hashlib.sha256((stage/'inventory.json').read_bytes()).hexdigest()==a['inventory_sha256']
i=json.loads((stage/'inventory.json').read_bytes())
for name,f in i['files'].items():
 p=stage/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']and stat.S_IMODE(p.stat().st_mode)==f['mode'],name
for name,m in i['directories'].items():assert stat.S_IMODE((stage/name).stat().st_mode)==m,name
assert not(stage/'trial-1').exists()
with(stage/'trial-1-admission.json').open('xb')as out:out.write(raw)
marker=stage/'trial-1-consumed.json'
with marker.open('x')as out:json.dump({'admission_sha256':hashlib.sha256(raw).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},out);out.flush();os.fsync(out.fileno())
env=dict(os.environ,PYTHONPATH=str(stage),PYTHONDONTWRITEBYTECODE='1')
with(stage/'trial-1-controller.log').open('xb')as log:
 child=subprocess.Popen(a['command'],cwd=stage,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
receipt={'pid':child.pid,'admission_sha256':hashlib.sha256(raw).hexdigest(),'output':str(stage/'trial-1'),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':a['command']}
(stage/'trial-1-process.json').write_text(json.dumps(receipt,indent=2)+'\\n');print(json.dumps(receipt))
'''.replace('STAGE',repr(stage))
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','monster-gaming-pc.lan','python3 -c '+shlex.quote(remote)],input=raw,capture_output=True,timeout=30)
(p/'trial-1-launch.json').write_text(json.dumps({'exit':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()},indent=2)+'\n')
result.check_returncode();receipt=json.loads(result.stdout);(p/'trial-1-process.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
