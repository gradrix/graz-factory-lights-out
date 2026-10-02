import sys,json,subprocess,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from api import dispatch

def call(action,**kwargs):
    p=dict(kwargs,action=action);original=copy.deepcopy(p)
    result=dispatch(p)
    assert p==original, 'input mutated'
    return result

def reject(action,**kwargs):
    p=dict(kwargs,action=action);original=copy.deepcopy(p)
    try:dispatch(p)
    except ValueError:pass
    else:raise AssertionError('expected ValueError')
    assert p==original,'input mutated on rejection'

def cli(payload,expected):
    p=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(payload),capture_output=True,text=True)
    assert p.returncode==0,(p.returncode,p.stderr)
    assert json.loads(p.stdout)==expected,p.stdout
    assert not p.stderr,p.stderr

def cli_error(payload):
    p=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(payload),capture_output=True,text=True)
    assert p.returncode==2 and p.stderr.strip() and 'Traceback' not in p.stderr,(p.returncode,p.stderr)
    assert not p.stdout

assert dispatch({'action': 'attempts', 'outcomes': ['failed', 'ok']}) == 2
cli({'action': 'attempts', 'outcomes': ['failed', 'ok']}, 2)
reject("not-an-action")
cli_error({"action":"not-an-action"})

def s(**changes):
    p=dict(now=100,attempt=1,base=3,cap=10,max_attempts=8,outcome='transient');p.update(changes);return call('schedule',**p)
assert s()=={'retry':True,'at':103,'delay':3}
assert s(attempt=2)['delay']==6
assert s(attempt=3)['delay']==10
assert s(retry_after=50)['at']==150
assert s(retry_after=0)['delay']==3
for changes in [dict(outcome='success'),dict(outcome='permanent'),dict(attempt=8),dict(attempt=9)]:assert s(**changes)=={'retry':False,'at':None,'delay':None}
assert s(attempt=1000000,max_attempts=1000001)['delay']==10
for changes in [dict(base=0),dict(attempt=0),dict(cap=-1),dict(max_attempts=0),dict(retry_after=-1),dict(outcome='unknown')]:
    p=dict(now=0,attempt=1,base=1,cap=1,max_attempts=1,outcome='success');p.update(changes);reject('schedule',**p)
cli({'action':'schedule','now':10,'attempt':2,'base':2,'cap':20,'max_attempts':3,'outcome':'transient'},{'retry':True,'at':14,'delay':4})
