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

assert dispatch({'action': 'revision', 'document': {'revision': 1}}) == 1
cli({'action': 'revision', 'document': {'revision': 1}}, 1)
reject("not-an-action")
cli_error({"action":"not-an-action"})

d={'revision':1,'users':[{'id':'b','name':' B ','active':False},{'id':'a','name':'Á','active':True}],'meta':{'v':[1]}}
r=call('migrate',document=d)
assert r=={'revision':3,'accounts':{'b':{'profile':{'name':' B '},'enabled':False},'a':{'profile':{'name':'Á'},'enabled':True}},'order':['b','a'],'meta':{'v':[1]}}
assert call('migrate',document=r)==r
assert call('migrate',document={'revision':2,'users':[{'id':'x','profile':{'name':''},'enabled':False}]})=={'revision':3,'accounts':{'x':{'profile':{'name':''},'enabled':False}},'order':['x']}
assert call('migrate',document={'revision':1,'users':[]})=={'revision':3,'accounts':{},'order':[]}
reject('migrate',document={'revision':4})
reject('migrate',document={'revision':1,'users':[{'id':'a','name':'a','active':True},{'id':'a','name':'b','active':False}]})
p={'action':'migrate','document':r};copy=dispatch(p);copy['meta']['v'].append(2);assert r['meta']['v']==[1]
cli({'action':'migrate','document':{'revision':2,'users':[]}},{'revision':3,'accounts':{},'order':[]})
