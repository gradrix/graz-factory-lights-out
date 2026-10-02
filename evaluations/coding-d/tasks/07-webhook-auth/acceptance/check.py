import copy,json,pathlib,subprocess,sys,tempfile,sqlite3,unittest
sys.path.insert(0,str(pathlib.Path.cwd()))
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b

cases=[({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 105, 'tolerance': 5, 'signature': 'sha256=b6ae95232f7a6f10ed56c0c2931bda6344efb9e66d09bf79943ca1df746bbddf'}, True), ({'action': 'verify', 'secret': 'é', 'body': '猫\n', 'timestamp': 0, 'now': 0, 'tolerance': 0, 'signature': 'sha256=6745333ad1bd28156fb8fe5136e126b0af176a14850bcd743711191fec27c7e4'}, True), ({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 94, 'tolerance': 5, 'signature': 'sha256=b6ae95232f7a6f10ed56c0c2931bda6344efb9e66d09bf79943ca1df746bbddf'}, False), ({'action': 'verify', 'secret': '', 'body': '', 'timestamp': 1099511627776, 'now': 1099511627776, 'tolerance': 0, 'signature': 'sha256=55851ce14b1cb00f4a5d26aa0de99989226d7abf64a0cb5ed993f5807a69876b'}, True), ({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 100, 'tolerance': 0, 'signature': ''}, False), ({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 100, 'tolerance': 0, 'signature': 'sha256=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'}, False), ({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 100, 'tolerance': 0, 'signature': 'sha256=0000000000000000000000000000000000000000000000000000000000000000'}, False), ({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 100, 'tolerance': 0, 'signature': 'sha256=é'}, False), ({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 100, 'tolerance': 0, 'signature': 'sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}, False)]
errors=[]
database=False
new_action='verify'
old_payload={'action': 'body_bytes', 'body': 'é猫'}
old_expected=5
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
