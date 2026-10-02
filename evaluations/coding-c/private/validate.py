import pathlib,json,tempfile,subprocess,hashlib
R=pathlib.Path(__file__).resolve().parents[1];image='sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578'
records=[]
for d in sorted((R/'tasks').iterdir()):
 for kind in ['baseline','reference']:
  with tempfile.TemporaryDirectory(dir=R/"private") as tmp:
   w=d/'source' if kind=='baseline' else pathlib.Path(tmp)
   if kind=='reference':
    w.chmod(0o755)
    for name,c in json.loads((R/'private'/f'{d.name[:2]}-reference.json').read_text()).items():(w/name).write_text(c)
   p=subprocess.run(['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','2','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-v',f'{d}/acceptance:/acceptance:ro','-w','/workspace',image,'python','-B','-I','/acceptance/check.py'],capture_output=True,text=True,timeout=45)
   ok=p.returncode==0 if kind=='reference' else p.returncode!=0 and 'ValueError: unknown action:' in p.stderr
   print(d.name,kind,p.returncode,ok,flush=True)
   records.append({'task':d.name,'kind':kind,'exit_code':p.returncode,'expected_outcome_confirmed':ok,'stdout':p.stdout,'stderr':p.stderr})
version=subprocess.check_output(['docker','run','--rm','--pull','never','--network','none',image,'python','--version'],text=True).strip()
(R/'private/validation.json').write_text(json.dumps({'image':image,'python':version,'outcomes':records},indent=2)+'\n')
assert all(r['expected_outcome_confirmed'] for r in records)
