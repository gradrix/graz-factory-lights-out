import json,pathlib,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parents[1]
IMAGE='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
mutations=[('07-webhook-auth','integer_boolean','return hmac.compare_digest(sig[7:],expected)','return int(hmac.compare_digest(sig[7:],expected))','API wrong result/type'),('04-sqlite-stock','autocommit_breaks_rollback',"con=sqlite3.connect(p['db'])","con=sqlite3.connect(p['db'],isolation_level=None)",'persistence/atomicity'),('11-support-redaction','alias_unredacted_containers','def feature(p):','def feature(p):\n if not p["keys"]:return p["document"]','aliased input containers')]
records=[]
for task,name,old,new,marker in mutations:
 files=json.loads((R/'private'/f'{task[:2]}-reference.json').read_text());assert old in files['domain.py'];files['domain.py']=files['domain.py'].replace(old,new)
 with tempfile.TemporaryDirectory(dir=R/'private') as tmp:
  w=pathlib.Path(tmp);w.chmod(0o755)
  for f,c in files.items():(w/f).write_text(c)
  proc=subprocess.run(['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','2','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-v',f'{R}/tasks/{task}/acceptance:/acceptance:ro','-w','/workspace',IMAGE,'python','-B','-I','/acceptance/check.py'],capture_output=True,text=True,timeout=60)
  ok=proc.returncode!=0 and marker in proc.stderr
  records.append({'task':task,'mutation':name,'exit_code':proc.returncode,'expected_outcome_confirmed':ok,'stdout':proc.stdout,'stderr':proc.stderr});print(task,name,ok,flush=True)
(R/'private/mutation-validation.json').write_text(json.dumps({'image':IMAGE,'outcomes':records},indent=2)+'\n')
assert all(x['expected_outcome_confirmed'] for x in records)
