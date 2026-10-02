import json,pathlib,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parents[1]
IMAGE='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
metadata=json.loads(subprocess.check_output(['docker','run','--rm','--pull','never','--network','none',IMAGE,'python','-c','import sys,json,platform;print(json.dumps({"version":platform.python_version(),"sys_version":sys.version,"implementation":platform.python_implementation()}))'],text=True))
assert metadata['version']=='3.12.13'
records=[]
for d in sorted((R/'tasks').iterdir()):
 ref=json.loads((R/'private'/f'{d.name[:2]}-reference.json').read_text())
 for kind in ['baseline','reference','missing_tests','failing_tests','unchanged_docs']:
  with tempfile.TemporaryDirectory(dir=R/'private') as tmp:
   w=d/'source' if kind=='baseline' else pathlib.Path(tmp);w.chmod(0o755)
   if kind!='baseline':
    files=dict(ref)
    if kind=='missing_tests':del files['test_behavior.py']
    if kind=='failing_tests':files['test_behavior.py']+='\nclass BrokenRegression(unittest.TestCase):\n def test_failure(self):self.fail("deliberately broken generated test")\n'
    if kind=='unchanged_docs':files['README.md']=(d/'source/README.md').read_text()
    for name,s in files.items():(w/name).write_text(s)
   proc=subprocess.run(['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','2','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-v',f'{d}/acceptance:/acceptance:ro','-w','/workspace',IMAGE,'python','-B','-I','/acceptance/check.py'],capture_output=True,text=True,timeout=60)
   marker={'baseline':'ValueError: unknown action:','missing_tests':'need three discoverable tests','failing_tests':'generated tests failed','unchanged_docs':'document new CLI usage'}.get(kind)
   ok=proc.returncode==0 if kind=='reference' else proc.returncode!=0 and marker in proc.stderr
   records.append({'task':d.name,'kind':kind,'exit_code':proc.returncode,'expected_outcome_confirmed':ok,'stdout':proc.stdout,'stderr':proc.stderr})
   print(d.name,kind,proc.returncode,ok,flush=True)
(R/'private/validation.json').write_text(json.dumps({'image':IMAGE,'environment':metadata,'outcomes':records},indent=2)+'\n')
assert all(x['expected_outcome_confirmed'] for x in records)
