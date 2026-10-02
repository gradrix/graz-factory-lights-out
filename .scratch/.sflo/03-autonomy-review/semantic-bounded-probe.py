import pathlib,json,tempfile,subprocess,hashlib,os
root=pathlib.Path(__file__).resolve().parents[3];fixture=root/'.gflo/review-qualification-v2'; out=pathlib.Path(__file__).parent
runtime='/home/gradrix/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/bin/python3.12'
results=[]
for p in sorted((fixture/'private/review').glob('*.json'))+[fixture/'private/supplemental-money-oracle.json']:
 d=json.loads(p.read_text())
 with tempfile.TemporaryDirectory() as tmp:
  t=pathlib.Path(tmp)
  for n,v in d['files'].items():(t/n).write_text(v)
  (t/'check.py').write_text(d['executable_assertions'])
  proc=subprocess.run([runtime,'-B','check.py'],cwd=t,capture_output=True,text=True)
  assert bool(proc.returncode)==(d['expected_verdict']=='block'),(d['id'],proc.stderr)
  results.append({'id':d['id'],'supplemental':p.name.startswith('supplemental'),'expected':d['expected_verdict'],'exit':proc.returncode,'stderr':proc.stderr})
for name,source,args,env in [
 ('python312-Z',"from datetime import datetime; print(datetime.fromisoformat('2024-01-01T00:00:00Z'))",[],None),
 ('utf8-default',"import locale; print(locale.getencoding()); print(open('utf8.txt').read())",[],None),
 ('ascii-portability',"import locale; print(locale.getencoding()); print(open('utf8.txt').read())",['-X','utf8=0'],dict(os.environ,LC_ALL='C',PYTHONCOERCECLOCALE='0')),
 ('ascii-explicit-utf8-control',"assert open('utf8.txt',encoding='utf-8').read() == chr(233)",['-X','utf8=0'],dict(os.environ,LC_ALL='C',PYTHONCOERCECLOCALE='0')),
 ]:
 with tempfile.TemporaryDirectory() as tmp:
  pathlib.Path(tmp,'utf8.txt').write_bytes(bytes([0xc3,0xa9]))
  proc=subprocess.run([runtime,*args,'-c',source],cwd=tmp,capture_output=True,text=True,env=env)
  results.append({'probe':name,'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
ns={};d=json.loads((fixture/'private/supplemental-money-oracle.json').read_text());exec(d['files']['core.py'],ns)
results.append({'probe':'supplemental negative zero example','actual':ns['total'](['-0.001']),'claimed':'-0.00'})
(out/'semantic-bounded-probes.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results[-5:],indent=2));print('review sha256',hashlib.sha256((out/'flash-bounded.json').read_bytes()).hexdigest())
