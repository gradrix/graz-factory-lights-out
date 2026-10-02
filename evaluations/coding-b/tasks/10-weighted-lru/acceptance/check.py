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

assert dispatch({'action': 'weight', 'entries': [{'weight': 2}, {'weight': 3}]}) == 5
cli({'action': 'weight', 'entries': [{'weight': 2}, {'weight': 3}]}, 5)
reject("not-an-action")
cli_error({"action":"not-an-action"})

def put(k,w,v=None):return {'op':'put','key':k,'weight':w,'value':v}
def get(k):return {'op':'get','key':k}
r=call('cache',capacity=5,operations=[put('a',2,1),put('b',2,2),get('a'),put('c',3,3),get('b')])
assert r['results']==[{'stored':True,'evicted':[]},{'stored':True,'evicted':[]},{'hit':True,'value':1},{'stored':True,'evicted':['b']},{'hit':False,'value':None}]
assert [x['key'] for x in r['entries']]==['a','c']
r=call('cache',capacity=4,operations=[put('a',1),put('b',1),put('a',5),put('c',3)])
assert r['results'][2]=={'stored':False,'evicted':[]} and r['results'][3]['evicted']==['a']
assert [x['key'] for x in r['entries']]==['b','c']
r=call('cache',capacity=5,operations=[put('a',1),put('b',1),put('c',1),put('d',5)])
assert r['results'][-1]['evicted']==['a','b','c']
r=call('cache',capacity=3,operations=[put('a',1),put('b',1),put('a',2)])
assert [x['key'] for x in r['entries']]==['b','a'] and not r['results'][-1]['evicted']
assert call('cache',capacity=0,operations=[put('a',1),get('a')])=={'results':[{'stored':False,'evicted':[]},{'hit':False,'value':None}],'entries':[]}
reject('cache',capacity=-1,operations=[]);reject('cache',capacity=0,operations=[put('a',0)])
cli({'action':'cache','capacity':0,'operations':[]},{'results':[],'entries':[]})
