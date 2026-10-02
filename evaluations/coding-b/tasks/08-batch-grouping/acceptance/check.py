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

assert dispatch({'action': 'ids', 'items': [{'id': 'b'}, {'id': 'a'}, {'id': 'b'}]}) == ['b', 'a', 'b']
cli({'action': 'ids', 'items': [{'id': 'b'}, {'id': 'a'}, {'id': 'b'}]}, ['b', 'a', 'b'])
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('group',requested=['a','b','c','d'],responses=[{'id':'c','ok':False,'error':'bad'},{'id':'b','ok':True,'value':0},{'id':'a','ok':True,'value':None}])=={'successes':[{'id':'a','value':None},{'id':'b','value':0}],'failures':[{'id':'c','error':'bad'}],'missing':['d']}
assert call('group',requested=[],responses=[])=={'successes':[],'failures':[],'missing':[]}
reject('group',requested=['x','x'],responses=[])
reject('group',requested=['x'],responses=[{'id':'y','ok':True,'value':1}])
reject('group',requested=['x'],responses=[{'id':'x','ok':True,'value':1},{'id':'x','ok':False,'error':'bad'}])
import itertools
responses=[{'id':'a','ok':True,'value':False},{'id':'b','ok':False,'error':''},{'id':'c','ok':True,'value':''}]
for order in itertools.permutations(responses):
    result=call('group',requested=['c','b','a'],responses=list(order));assert result['successes']==[{'id':'c','value':''},{'id':'a','value':False}] and result['failures']==[{'id':'b','error':''}]
cli({'action':'group','requested':['x'],'responses':[]},{'successes':[],'failures':[],'missing':['x']})
