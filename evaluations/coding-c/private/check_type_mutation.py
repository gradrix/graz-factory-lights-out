import hashlib,json,pathlib,subprocess,tempfile
r=pathlib.Path(__file__).resolve().parents[1]
image='sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578'
reference=json.loads((r/'private/06-reference.json').read_text())
records=[]
for kind in ['reference','integer_boolean_mutant']:
 with tempfile.TemporaryDirectory(dir=r/'private') as directory:
  w=pathlib.Path(directory);w.chmod(0o755)
  files=dict(reference)
  if kind=='integer_boolean_mutant':
   files['domain.py']=files['domain.py'].replace("return bool(s) and valid(s)","return int(bool(s) and valid(s))")
   assert files['domain.py']!=reference['domain.py']
  for name,content in files.items():(w/name).write_text(content)
  proc=subprocess.run(['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','2','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-v',f'{r}/tasks/06-luhn-check/acceptance:/acceptance:ro','-w','/workspace',image,'python','-B','-I','/acceptance/check.py'],capture_output=True,text=True,timeout=45)
  confirmed=proc.returncode==0 if kind=='reference' else proc.returncode!=0 and 'wrong result' in proc.stderr
  records.append({'kind':kind,'exit_code':proc.returncode,'expected_outcome_confirmed':confirmed,'domain_sha256':hashlib.sha256(files['domain.py'].encode()).hexdigest(),'stdout':proc.stdout,'stderr':proc.stderr})
(r/'private/type-mutation-validation.json').write_text(json.dumps({'image':image,'outcomes':records},indent=2)+'\n')
assert all(x['expected_outcome_confirmed'] for x in records)
print(json.dumps(records,indent=2))
