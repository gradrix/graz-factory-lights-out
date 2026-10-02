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

assert dispatch({'action': 'keys', 'config': {'z': 1, 'a': 2}}) == ['a', 'z']
cli({'action': 'keys', 'config': {'z': 1, 'a': 2}}, ['a', 'z'])
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('resolve',defaults={'a':1,'n':{'x':1,'y':2},'l':[1],'z':None},layers=[{'n':{'x':None,'q':3},'l':[2]},{'a':4,'n':{'y':5}}],required=['z'])=={'a':4,'n':{'y':5,'q':3},'l':[2],'z':None}
assert call('resolve',defaults={'n':1},layers=[{'n':{'ghost':None,'x':2}}],required=[])=={'n':{'x':2}}
assert call('resolve',defaults={},layers=[{'absent':None},{'new':{'gone':None}}],required=[])=={'new':{}}
reject('resolve',defaults={'a':1},layers=[{'a':None}],required=['a'])
p={'action':'resolve','defaults':{'x':[1]},'layers':[],'required':[]};r=dispatch(p);r['x'].append(2);assert p['defaults']['x']==[1]
p={'action':'resolve','defaults':{},'layers':[{'x':[1]}],'required':[]};r=dispatch(p);r['x'].append(2);assert p['layers'][0]['x']==[1]
cli({'action':'resolve','defaults':{'a':1},'layers':[{'a':2}],'required':['a']},{'a':2})
