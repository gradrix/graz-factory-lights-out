import copy,json,pathlib,subprocess,sys,tempfile,sqlite3,unittest
sys.path.insert(0,str(pathlib.Path.cwd()))
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b

cases=[({'action': 'select', 'artifacts': [{'id': 'a', 'platform': 'linux', 'version': '1.9.9', 'yanked': False}, {'id': 'b', 'platform': 'linux', 'version': '1.10.0', 'yanked': False}, {'id': 'c', 'platform': 'linux', 'version': '2.0.0', 'yanked': False}], 'platform': 'linux', 'major': 1}, {'id': 'b', 'version': '1.10.0'}), ({'action': 'select', 'artifacts': [{'id': 'z', 'platform': 'x', 'version': '0.1.0', 'yanked': False}, {'id': 'a', 'platform': 'x', 'version': '0.1.0', 'yanked': False}, {'id': 'y', 'platform': 'x', 'version': '0.2.0', 'yanked': True}], 'platform': 'x', 'major': 0}, {'id': 'a', 'version': '0.1.0'}), ({'action': 'select', 'artifacts': [], 'platform': 'x', 'major': 1}, None), ({'action': 'select', 'artifacts': [{'id': 'a', 'platform': 'mac', 'version': '1.0.0', 'yanked': False}], 'platform': 'linux', 'major': 1}, None)]
errors=[]
database=False
new_action='select'
old_payload={'action': 'artifact_ids', 'artifacts': [{'id': 'b'}, {'id': 'a'}]}
old_expected=['b', 'a']
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
