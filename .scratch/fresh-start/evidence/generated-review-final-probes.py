import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp/gflo-review-candidate2')
from gflo.sandbox import Sandbox
ROOT=Path(__file__).parent
s=Sandbox()
runs={'invoice':ROOT/'repairs-128k/runs/41fbdafe38ff','inventory':ROOT/'repairs-128k/runs/ff554c2e0dfd','log-summary':ROOT/'pilot-128k/runs/cb7453d0b5d0'}
probes={'invoice':r'''
import subprocess,pathlib,json,io,invoice
valids=[('customer,amount\n',{}),('customer,amount\n" Alice ",1.235\nAlice,-1.235\n"Comma, Name",0\n',{' Alice ':'1.24','Alice':'-1.24','Comma, Name':'0.00'}),('customer,amount\nA,0.005\nA,0.005\nA,-0.02\n',{'A':'0.00'})]
invalids=['','customer,amount\nAlice\n','customer,amount\nAlice,\n','customer,amount\n"   ",1\n','customer,amount\nAlice,NaN\n','customer,amount\nAlice,Infinity\n','customer,amount\nAlice,nope\n','customer\nAlice\n']
for text,expected in valids:
 assert invoice.summarize(io.StringIO(text))==expected
 p=pathlib.Path('/tmp/input.csv');p.write_text(text)
 r=subprocess.run(['python','invoice.py',str(p)],capture_output=True,text=True)
 assert r.returncode==0 and json.loads(r.stdout)==expected,(text,r)
for text in invalids:
 p=pathlib.Path('/tmp/input.csv');p.write_text(text)
 r=subprocess.run(['python','invoice.py',str(p)],capture_output=True,text=True)
 assert r.returncode==2 and r.stderr.strip() and 'Traceback' not in r.stderr and not r.stdout,(text,r)
print('GR-01 GR-02 QUOTED_WHITESPACE_AND_ADJACENT_CONTROLS_PASS')
''','inventory':r'''
import store,subprocess,json,pathlib
source=pathlib.Path('store.py').read_text()
assert '_GUARD_PAD' not in source and 'cur.fetchone is not None' not in source
p='/tmp/inventory.db';store.initialize(p);store.put(p,'X',5)
a=[subprocess.Popen(['python','cli.py',p,'reserve','X','4'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
results=[]
for child in a:
 out,err=child.communicate();assert child.returncode==0 and not err;results.append(json.loads(out))
assert sum(r['reserved'] for r in results)==1 and store.available(p,'X')==1,results
assert not store.reserve(p,'X',2) and store.available(p,'X')==1
assert not store.reserve(p,'missing',1) and store.available(p,'missing') is None
for value in [0,-1,True,False,1.5,'1',None]:assert not store.reserve(p,'X',value)
for value in ['0','-1','nope','1.5']:
 r=subprocess.run(['python','cli.py',p,'reserve','X',value],capture_output=True,text=True)
 assert r.returncode==2 and r.stderr and 'Traceback' not in r.stderr
store.put(p,'X',9);assert store.available(p,'X')==9
print('GR-03_SIMPLICITY_CONCURRENT_PROCESSES_AND_CONTROLS_PASS')
'''}
for name,run in runs.items():
 w=run/'workspace'
 print('CANDIDATE',name,run.name,json.dumps({str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(w.rglob('*')) if p.is_file()},sort_keys=True),flush=True)
 task=json.loads((run/'task.json').read_text())
 result=s.verify(w,task,run/'acceptance');print('CONFIGURED_ACCEPTANCE',name,json.dumps(result),flush=True);assert result['passed']
 if name in probes:
  result=s.execute(w,['python','-c',probes[name]],acceptance=run/'acceptance')
  print('INDEPENDENT_SEMANTIC',name,json.dumps(result),flush=True);assert result['exit_code']==0
print('ALL_RECHECKS_PASS')
