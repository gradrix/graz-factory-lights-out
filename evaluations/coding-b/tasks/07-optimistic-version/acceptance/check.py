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

assert dispatch({'action': 'read', 'records': {'x': {'version': 2, 'data': {'a': 1}}}, 'id': 'x'}) == {'version': 2, 'data': {'a': 1}}
cli({'action': 'read', 'records': {'x': {'version': 2, 'data': {'a': 1}}}, 'id': 'x'}, {'version': 2, 'data': {'a': 1}})
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('update',records={},id='a',expected=None,patch={'x':1})=={'applied':True,'records':{'a':{'version':1,'data':{'x':1}}},'record':{'version':1,'data':{'x':1}}}
r={'a':{'version':2,'data':{'x':1,'y':2}}}
assert call('update',records=r,id='a',expected=2,patch={'x':None})['record']=={'version':3,'data':{'x':None,'y':2}}
for expected in [None,0,1,3]:
    got=call('update',records=r,id='a',expected=expected,patch={'bad':3});assert not got['applied'] and got['records']==r
assert call('update',records={},id='a',expected=0,patch={})=={'applied':False,'records':{},'record':None}
p={'action':'update','records':{'a':{'version':0,'data':{'nested':[1]}}},'id':'a','expected':0,'patch':{'new':[2]}}
got=dispatch(p);got['record']['data']['nested'].append(9);got['records']['a']['data']['new'].append(8)
assert p['records']['a']['data']['nested']==[1] and p['patch']['new']==[2]
assert got['records']['a']['data']['nested']==[1]
assert call('read',records={},id='absent') is None
cli({'action':'update','records':{},'id':'x','expected':None,'patch':{}},{'applied':True,'records':{'x':{'version':1,'data':{}}},'record':{'version':1,'data':{}}})
