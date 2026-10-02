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

assert dispatch({'action': 'count', 'events': [3, 3, 5]}) == 3
cli({'action': 'count', 'events': [3, 3, 5]}, 3)
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('admit',history=[0,5,5],now=10,window=10,limit=3)=={'allowed':True,'history':[5,5,10],'retry_at':None}
assert call('admit',history=[5,5],now=10,window=10,limit=2)=={'allowed':False,'history':[5,5],'retry_at':15}
assert call('admit',history=[1,2,3,4],now=5,window=10,limit=2)=={'allowed':False,'history':[1,2,3,4],'retry_at':13}
assert call('admit',history=[0],now=100,window=10,limit=0)=={'allowed':False,'history':[],'retry_at':None}
assert call('admit',history=[-5],now=0,window=5,limit=1)['history']==[0]
for kwargs in [dict(history=[2,1],now=2,window=1,limit=1),dict(history=[3],now=2,window=1,limit=1),dict(history=[],now=0,window=0,limit=1),dict(history=[],now=0,window=1,limit=-1)]:reject('admit',**kwargs)
for history in [[],[0],[0,0],[0,1,2],[2,2,2,2]]:
    for limit in range(4):
        r=call('admit',history=history,now=2,window=3,limit=limit)
        if not r['allowed'] and limit:
            t=r['retry_at'];assert sum(x>t-3 for x in history)<limit
            assert sum(x>(t-1)-3 for x in history)>=limit
cli({'action':'admit','history':[1],'now':2,'window':3,'limit':1},{'allowed':False,'history':[1],'retry_at':4})
