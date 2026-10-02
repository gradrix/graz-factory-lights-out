import hashlib,json,pathlib,subprocess,tempfile
R=pathlib.Path('.gflo/coding-qualification-d').resolve();E=pathlib.Path('.scratch/.sflo/03-autonomy-review').resolve();expected='da7a8d364c326a61bb8c22f0873188c0498d98213a676c23107c1d730a143d0b'
assert hashlib.sha256((R/'manifest.json').read_bytes()).hexdigest()==expected
m=json.loads((R/'manifest.json').read_text());assert len(m['sha256'])==99
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in m['sha256'].items())
image=m['environment']['image'];assert image=='sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
version=subprocess.check_output(['docker','run','--rm','--pull','never','--network','none',image,'python','-c','import platform;print(platform.python_version())'],text=True).strip();assert version=='3.12.13';print('manifest99/runtime confirmed',flush=True)
results=[]
def run(n,label,mutate=lambda f:None):
 task=next((R/'tasks').glob(n+'-*'));files=json.loads((R/'private'/f'{n}-reference.json').read_text());mutate(files)
 with tempfile.TemporaryDirectory(prefix='gflo-cohort-d-qa-') as tmp:
  w=pathlib.Path(tmp);w.chmod(0o755)
  for name,contents in files.items():
   p=w/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(contents)
  command=['docker','run','--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','-e','PYTHONDONTWRITEBYTECODE=1','-v',f'{w}:/workspace:ro','-v',f'{task}/acceptance:/acceptance:ro','-w','/workspace',image,'python','-B','-I','/acceptance/check.py']
  p=subprocess.run(command,capture_output=True,text=True,timeout=60);results.append(dict(task=task.name,label=label,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));print(n,label,p.returncode,flush=True)
for n in ['04','07','09','11']:run(n,'reference')
run('04','commit-every-update',lambda f:f.update({'domain.py':f['domain.py'].replace("(row[0]+item['delta'],item['sku']))","(row[0]+item['delta'],item['sku']));con.commit()")}))
run('04','commit-every-update-cli-only',lambda f:f.update({'domain.py':f['domain.py'].replace("(row[0]+item['delta'],item['sku']))","(row[0]+item['delta'],item['sku']));con.commit() if __import__('sys').argv[0].endswith('cli.py') else None")}))
run('07','integer-boolean-cli-only',lambda f:f.update({'cli.py':f['cli.py'].replace('json.dumps(result','json.dumps(int(result) if type(result) is bool else result')}))
run('09','lf-records',lambda f:f.update({'domain.py':f['domain.py'].replace("lineterminator='\\r\\n'","lineterminator='\\n'")}))
run('11','unchanged-list-alias',lambda f:f.update({'domain.py':f['domain.py'].replace("names={k.casefold() for k in p['keys']}","names={k.casefold() for k in p['keys']}\n if not names:return p['document']")}))
run('07','missing-docs',lambda f:f.update({'README.md':'# Old API'}))
run('07','failing-tests',lambda f:f.update({'test_added_failure.py':'import unittest\nclass Broken(unittest.TestCase):\n def test_broken(self):self.fail("QA expected rejection")\n'}))
(E/'qa-cohort-d-probe.json').write_text(json.dumps(dict(manifest=expected,image=image,version=version,results=results),indent=2)+'\n')
assert all((r['exit']==0)==(r['label']=='reference') for r in results),results
assert hashlib.sha256((R/'manifest.json').read_bytes()).hexdigest()==expected
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in m['sha256'].items())
print('PASS controls/mutants; frozen files unchanged')
