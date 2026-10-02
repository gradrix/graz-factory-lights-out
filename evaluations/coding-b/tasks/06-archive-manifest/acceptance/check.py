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

assert dispatch({'action': 'sizes', 'entries': [{'size': 3}, {'size': 0}, {'size': 2}]}) == 5
cli({'action': 'sizes', 'entries': [{'size': 3}, {'size': 0}, {'size': 2}]}, 5)
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('validate',entries=[{'path':'./b//x','size':3},{'path':'a','size':2}],max_total=5)=={'files':[{'path':'a','size':2},{'path':'b/x','size':3}],'total':5}
assert call('validate',entries=[],max_total=0)=={'files':[],'total':0}
for path in ['', '/', '../x','a/../b','a\\b','C:x','x\x00y','.','//host/x']:
    reject('validate',entries=[{'path':path,'size':0}],max_total=10)
for entries in [[{'path':'a//b','size':1},{'path':'a/./b','size':1}],[{'path':'a/b','size':1},{'path':'a','size':1}],[{'path':'a','size':-1}]]:
    reject('validate',entries=entries,max_total=10)
reject('validate',entries=[{'path':'a','size':2}],max_total=1)
reject('validate',entries=[],max_total=-1)
assert call('validate',entries=[{'path':'a','size':1},{'path':'ab/x','size':1}],max_total=2)['total']==2
cli({'action':'validate','entries':[{'path':'./a','size':1}],'max_total':1},{'files':[{'path':'a','size':1}],'total':1})
