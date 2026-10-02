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

assert dispatch({'action': 'sources', 'events': [{'source': 'b'}, {'source': 'a'}, {'source': 'b'}]}) == ['a', 'b']
cli({'action': 'sources', 'events': [{'source': 'b'}, {'source': 'a'}, {'source': 'b'}]}, ['a', 'b'])
reject("not-an-action")
cli_error({"action":"not-an-action"})

def event(s,n,d=None):return {'source':s,'seq':n,'data':d}
r=call('ingest',watermarks={'a':1,'idle':9},events=[event('a',4),event('b',2),event('a',2),event('b',1),event('a',2)])
assert r=={'watermarks':{'a':2,'idle':9,'b':2},'released':[event('a',2),event('b',1),event('b',2)],'pending':[event('a',4)]}
r=call('ingest',watermarks={'a':2},events=[event('a',1,'x'),event('a',1,'y'),event('z',3)])
assert r=={'watermarks':{'a':2,'z':0},'released':[],'pending':[event('z',3)]}
reject('ingest',watermarks={},events=[event('a',2,1),event('a',2,2)])
assert call('ingest',watermarks={},events=[])=={'watermarks':{},'released':[],'pending':[]}
import itertools
items=[event('a',1,{'v':[1]}),event('a',2),event('b',2)]
expected={'watermarks':{'a':2,'b':0},'released':items[:2],'pending':items[2:]}
for perm in itertools.permutations(items):assert call('ingest',watermarks={},events=list(perm))==expected
cli({'action':'ingest','watermarks':{},'events':[event('a',2)]},{'watermarks':{'a':0},'released':[],'pending':[event('a',2)]})
