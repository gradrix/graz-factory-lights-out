import copy,importlib,json,pathlib,subprocess,sys,unittest
sys.path.insert(0,str(pathlib.Path.cwd()))
from api import dispatch
def json_equal(actual,expected):
 if type(actual) is not type(expected):return False
 if isinstance(expected,dict):return actual.keys()==expected.keys() and all(json_equal(actual[k],expected[k]) for k in expected)
 if isinstance(expected,list):return len(actual)==len(expected) and all(json_equal(a,b) for a,b in zip(actual,expected))
 return actual==expected
cases=[({'action': 'occurrences', 'start': '2024-01-31', 'day': 31, 'count': 3}, ['2024-01-31', '2024-02-29', '2024-03-31']), ({'action': 'occurrences', 'start': '2023-02-28', 'day': 31, 'count': 2}, ['2023-02-28', '2023-03-31']), ({'action': 'occurrences', 'start': '2024-12-20', 'day': 10, 'count': 2}, ['2025-01-10', '2025-02-10']), ({'action': 'occurrences', 'start': '2024-01-01', 'day': 1, 'count': 0}, []), ({'action': 'occurrences', 'start': '2024-02-29', 'day': 28, 'count': 2}, ['2024-03-28', '2024-04-28'])]
errors=[]
baseline={'action':'identity','value':{'nested':[1,None,'é',True,False]}}
assert json_equal(dispatch(baseline),baseline['value'])
for p,expected in cases:
 original=copy.deepcopy(p)
 assert json_equal(dispatch(p),expected),(p,'wrong result')
 assert json_equal(p,original),'mutated payload'
 proc=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(p),text=True,capture_output=True,timeout=5)
 assert proc.returncode==0,proc.stderr
 assert json_equal(json.loads(proc.stdout),expected)
for p in errors+[{'action':'unknown'}]:
 original=copy.deepcopy(p)
 try:dispatch(p)
 except ValueError:pass
 else:raise AssertionError('expected ValueError')
 assert json_equal(p,original),'mutated failed input'
 proc=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(p),text=True,capture_output=True,timeout=5)
 assert proc.returncode==2 and proc.stderr.strip() and 'Traceback' not in proc.stderr
proc=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(baseline),text=True,capture_output=True,timeout=5)
assert proc.returncode==0 and json_equal(json.loads(proc.stdout),baseline['value'])
suite=unittest.defaultTestLoader.discover('.')
assert suite.countTestCases()>=3,'need three discoverable regression tests'
result=unittest.TextTestRunner(verbosity=1).run(suite)
assert result.wasSuccessful(),'generated tests failed'
readme=pathlib.Path('README.md').read_text()
assert len(readme.split())>=40 and 'cli.py' in readme and all(a in readme for a in ['occurrences']),'document new CLI usage'
print('PASS')
