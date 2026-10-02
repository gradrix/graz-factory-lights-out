import copy,importlib,json,pathlib,subprocess,sys,unittest
sys.path.insert(0,str(pathlib.Path.cwd()))
from api import dispatch
def json_equal(actual,expected):
 if type(actual) is not type(expected):return False
 if isinstance(expected,dict):return actual.keys()==expected.keys() and all(json_equal(actual[k],expected[k]) for k in expected)
 if isinstance(expected,list):return len(actual)==len(expected) and all(json_equal(a,b) for a,b in zip(actual,expected))
 return actual==expected
cases=[({'action': 'tally', 'candidates': ['b', 'a', 'c'], 'ballots': [['a', 'a'], ['b'], []]}, [{'candidate': 'b', 'votes': 1}, {'candidate': 'a', 'votes': 1}, {'candidate': 'c', 'votes': 0}]), ({'action': 'tally', 'candidates': [], 'ballots': [[]]}, []), ({'action': 'tally', 'candidates': ['x', 'y'], 'ballots': [['y'], ['y'], ['x']]}, [{'candidate': 'y', 'votes': 2}, {'candidate': 'x', 'votes': 1}]), ({'action': 'tally', 'candidates': ['z', 'a', 'b'], 'ballots': []}, [{'candidate': 'z', 'votes': 0}, {'candidate': 'a', 'votes': 0}, {'candidate': 'b', 'votes': 0}])]
errors=[{'action': 'tally', 'candidates': ['a'], 'ballots': [['a'], ['z']]}]
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
assert len(readme.split())>=40 and 'cli.py' in readme and all(a in readme for a in ['tally']),'document new CLI usage'
print('PASS')
