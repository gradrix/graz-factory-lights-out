import copy,json,pathlib,subprocess,sys,tempfile,sqlite3,unittest
sys.path.insert(0,str(pathlib.Path.cwd()))
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b

cases=[({'action': 'report', 'entries': [{'route': '/b', 'status': 503, 'ms': 90}, {'route': '/a', 'status': 404, 'ms': 0}, {'route': '/b', 'status': 200, 'ms': 10}], 'min_requests': 1}, [{'route': '/a', 'requests': 1, 'errors': 0, 'p95_ms': 0}, {'route': '/b', 'requests': 2, 'errors': 1, 'p95_ms': 90}]), ({'action': 'report', 'entries': [{'route': '/x', 'status': 200, 'ms': 1}, {'route': '/x', 'status': 200, 'ms': 2}, {'route': '/x', 'status': 200, 'ms': 3}, {'route': '/x', 'status': 200, 'ms': 4}, {'route': '/x', 'status': 200, 'ms': 5}, {'route': '/x', 'status': 200, 'ms': 6}, {'route': '/x', 'status': 200, 'ms': 7}, {'route': '/x', 'status': 200, 'ms': 8}, {'route': '/x', 'status': 200, 'ms': 9}, {'route': '/x', 'status': 200, 'ms': 10}, {'route': '/x', 'status': 200, 'ms': 11}, {'route': '/x', 'status': 200, 'ms': 12}, {'route': '/x', 'status': 200, 'ms': 13}, {'route': '/x', 'status': 200, 'ms': 14}, {'route': '/x', 'status': 200, 'ms': 15}, {'route': '/x', 'status': 200, 'ms': 16}, {'route': '/x', 'status': 200, 'ms': 17}, {'route': '/x', 'status': 200, 'ms': 18}, {'route': '/x', 'status': 200, 'ms': 19}, {'route': '/x', 'status': 200, 'ms': 20}], 'min_requests': 20}, [{'route': '/x', 'requests': 20, 'errors': 0, 'p95_ms': 19}]), ({'action': 'report', 'entries': [], 'min_requests': 1}, []), ({'action': 'report', 'entries': [{'route': '/x', 'status': 500, 'ms': 1}], 'min_requests': 2}, [])]
errors=[]
database=False
new_action='report'
old_payload={'action': 'routes', 'entries': [{'route': '/b', 'status': 200, 'ms': 1}, {'route': '/a', 'status': 200, 'ms': 2}]}
old_expected=['/b', '/a']
arena=tempfile.TemporaryDirectory()
counter=0
def prepare(p):
 global counter
 p=copy.deepcopy(p)
 if database:
  counter+=1;p['db']=str(pathlib.Path(arena.name)/('stock'+str(counter)+'.db'))
  with sqlite3.connect(p['db']) as con:
   con.execute('CREATE TABLE stock(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL)')
   con.executemany('INSERT INTO stock VALUES (?,?)',[('a',5),('b',2)])
 return p
def rows(p):
 with sqlite3.connect(p['db']) as con:return [{'sku':s,'quantity':q} for s,q in sorted(con.execute('SELECT sku,quantity FROM stock').fetchall())]
def check(p,want,error=False):
 original=prepare(p);given=copy.deepcopy(original)
 if error:
  try:dispatch(given)
  except ValueError:pass
  else:raise AssertionError('expected ValueError')
 else:
  actual=dispatch(given)
  assert json_equal(actual,want),(p,'API wrong result/type',actual,want)
  if new_action=='redact' and p['action']==new_action:
   def mutable_ids(x):
    ids={id(x)} if isinstance(x,(dict,list)) else set()
    for child in x.values() if isinstance(x,dict) else x if isinstance(x,list) else []:ids.update(mutable_ids(child))
    return ids
   assert not mutable_ids(actual)&mutable_ids(given['document']),'aliased input containers'
 assert json_equal(given,original),'mutated input'
 if database:assert json_equal(rows(given),old_expected if error else want),'persistence/atomicity'
 cp=prepare(p)
 proc=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(cp),text=True,capture_output=True,timeout=8)
 if error:assert proc.returncode==2 and proc.stderr.strip() and 'Traceback' not in proc.stderr and not proc.stdout.strip(),'CLI error contract'
 else:assert proc.returncode==0 and json_equal(json.loads(proc.stdout),want),(p,'CLI wrong result/type',proc.stdout,proc.stderr)
 if database:assert json_equal(rows(cp),old_expected if error else want),'CLI persistence/atomicity'
check(old_payload,old_expected)
for p,want in cases:check(p,want)
for p in errors:check(p,None,True)
check({'action':'unknown'},None,True)
suite=unittest.defaultTestLoader.discover('.')
assert suite.countTestCases()>=3,'need three discoverable tests'
result=unittest.TextTestRunner(verbosity=1).run(suite)
assert result.wasSuccessful(),'generated tests failed'
readme=pathlib.Path('README.md').read_text()
assert len(readme.split())>=40 and 'cli.py' in readme and new_action in readme,'document new CLI usage'
print('PASS')
