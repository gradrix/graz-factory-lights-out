import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp/gflo-review-candidate2')
from gflo.sandbox import Sandbox
ROOT=Path(__file__).parent/'pilot-128k/runs'
s=Sandbox()
probes={
'0b179de9a58a':r'''
import subprocess,pathlib,json
for label,text in [('valid','customer,amount\nAlice,1.235\n'),('empty-field','customer,amount\nAlice,\n'),('missing-field','customer,amount\nAlice\n'),('no-header','')]:
 p=pathlib.Path('/tmp/input.csv');p.write_text(text)
 r=subprocess.run(['python','invoice.py',str(p)],capture_output=True,text=True)
 if label=='valid':assert r.returncode==0 and json.loads(r.stdout)=={'Alice':'1.24'}
 if label=='empty-field':assert r.returncode==2 and 'Traceback' not in r.stderr
 if label=='missing-field':assert r.returncode==1 and 'AttributeError' in r.stderr
 if label=='no-header':assert r.returncode==0 and json.loads(r.stdout)=={}
 print(label,repr(r.returncode),repr(r.stdout),repr(r.stderr))
''',
'1ed0f9902508':r'''
import store,sqlite3,subprocess,json
p='/tmp/stock.db';store.initialize(p);store.put(p,'x',5)
assert store.reserve(p,'x',4) is True and store.available(p,'x')==1
assert store.reserve(p,'x',4) is False and store.available(p,'x')==1
assert store.reserve(p,'missing',1) is False
for q in ['0','-1','x']:
 r=subprocess.run(['python','cli.py',p,'reserve','x',q],capture_output=True,text=True)
 assert r.returncode==2 and 'Traceback' not in r.stderr
print('NORMAL_RESERVATION_AND_INVALID_QUANTITY_PASS')
with sqlite3.connect(p) as db:
 c=db.execute('UPDATE stock SET quantity=quantity WHERE sku=?',('absent',))
 assert c.fetchone is not None and c.rowcount==0
print('FETCHONE_ATTRIBUTE_IS_ALWAYS_PRESENT')
assert store._GUARD_PAD.count('AND 1')==400
print('400_NO_OP_SQL_PREDICATES')
''',
'cb7453d0b5d0':r'''
import subprocess,json,log_summary
text='\n{"service":" a ","level":" custom "}\n[]\n{bad}\n{"service":"b","level":"info"}\n'
r=subprocess.run(['python','log_summary.py','-'],input=text,capture_output=True,text=True)
assert r.returncode==0 and json.loads(r.stdout)=={'total':2,'invalid':2,'by_service':{'a':1,'b':1},'by_level':{'CUSTOM':1,'INFO':1}}
r=subprocess.run(['python','log_summary.py','-','--strict'],input=text,capture_output=True,text=True)
assert r.returncode==2 and not r.stdout and 'line 3' in r.stderr and 'Traceback' not in r.stderr
r=subprocess.run(['python','log_summary.py','/tmp/missing-log'],capture_output=True,text=True)
assert r.returncode==2 and not r.stdout and 'Traceback' not in r.stderr
class Stream:
 def __iter__(self):yield '{"service":"a","level":"ok"}'
 def read(self,*a):raise AssertionError('not streaming')
assert log_summary.summarize(Stream())['total']==1
print('MIXED_STRICT_MISSING_FILE_STREAMING_PASS')
'''}
for rid,code in probes.items():
 w=ROOT/rid/'workspace'
 hashes={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(w.rglob('*')) if p.is_file()}
 print('CANDIDATE',rid,json.dumps(hashes,sort_keys=True),flush=True)
 result=s.execute(w,['python','-c',code],acceptance=ROOT/rid/'acceptance')
 print(json.dumps(result),flush=True);assert result['exit_code']==0
