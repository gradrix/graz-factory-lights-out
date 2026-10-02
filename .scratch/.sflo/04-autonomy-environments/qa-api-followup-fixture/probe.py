import json,pathlib,hashlib,tempfile,subprocess,os,uuid
OUT=pathlib.Path(__file__).resolve().parent;R=pathlib.Path('.gflo/environment-api-followup').resolve();rows=[]
for path,digest in [('.gflo/environment-api-followup','72a7fd6eca78d476845c07f27ea143e75fbc0581758bd1f20a6e30c3421df193'),('.gflo/environment-api-followup-public','1accec55480d81d4467e0d6b96b5639ca43deb7444567fa3b7862a997085be34'),('.gflo/environment-coding-qualification-v2','858384ee7ca74724efe1ee4247c69cc039d88e8b53b344ef42c5f6c6d6e9989b'),('.gflo/environment-coding-qualification-v3','ff1ebb8b8846dcef0006f63f4afc5ff1149c941df8f4c130af098e06a6299d08')]:
 p=pathlib.Path(path);assert hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest()==digest
 for name,h in json.loads((p/'manifest.json').read_text())['sha256'].items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,(path,name)
old=pathlib.Path('.gflo/environment-coding-qualification-v2/tasks/python-api/acceptance/check.py').read_text();new=pathlib.Path('.gflo/environment-coding-qualification-v3/tasks/python-api/acceptance/check.py').read_text();assert old.replace(" and 'pip' in doc",'')==new
for kind in ['baseline','reference-extra','unbounded-at-original','unbounded-at-extra']:
 with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d);root.chmod(0o755);source=root/'source';source.mkdir();accept=root/'acceptance';accept.mkdir();files=json.loads((R/'private/reference.json').read_text())
  if kind=='baseline':files={str(p.relative_to(R/'source')):p.read_text() for p in (R/'source').rglob('*') if p.is_file() and '.git' not in p.parts}
  if kind.startswith('unbounded'):files['src/telemetry_usage/schemas.py']=files['src/telemetry_usage/schemas.py'].replace(' at:BoundedInt',' at:StrictInt')
  for name,data in files.items():p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
  oracle=(R/'acceptance/check.py').read_text()
  if kind.endswith('extra'):oracle=oracle.replace('  for p in invalid:',"  invalid.insert(0,dict(valid,samples=[{'device':'a','at':-1,'reading':0}]))\n  for p in invalid:")
  (accept/'check.py').write_text(oracle);name='gflo-followup-qa-'+uuid.uuid4().hex[:10]
  args=['docker','run','--rm','--pull','never','--runtime','runc','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--memory-swap','1g','--cpus','1','--pids-limit','128','--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/work:rw,nosuid,nodev,size=480m,mode=1777','--tmpfs','/tmp:rw,nosuid,nodev,size=16m,mode=1777','--env','TMPDIR=/work','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/opt/deps','--workdir','/tmp','--mount',f'type=bind,src={source},dst=/different/project,readonly','--mount',f'type=bind,src={accept},dst=/acceptance,readonly','--mount',f'type=bind,src={R.parent}/environment-locks/python-api/deps,dst=/opt/deps,readonly','sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc','python','-B','/acceptance/check.py','/different/project']
  try:r=subprocess.run(args,capture_output=True,text=True,timeout=120)
  finally:subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
  rows.append({'case':kind,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(kind,r.returncode,flush=True)
assert [r['exit']==0 for r in rows]==[False,True,True,False]
