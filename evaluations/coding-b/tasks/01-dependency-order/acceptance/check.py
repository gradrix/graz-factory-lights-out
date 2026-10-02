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

assert dispatch({'action': 'labels', 'nodes': [{'id': 'b'}, {'id': 'a'}]}) == ['b', 'a']
cli({'action': 'labels', 'nodes': [{'id': 'b'}, {'id': 'a'}]}, ['b', 'a'])
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('order',nodes=[]) == []
assert call('order',nodes=[{'id':'a','deps':['b']},{'id':'b','deps':[]},{'id':'c','deps':[]}]) == ['b','a','c']
assert call('order',nodes=[{'id':'c','deps':['a','a']},{'id':'a','deps':[]},{'id':'b','deps':['a']}]) == ['a','c','b']
reject('order',nodes=[{'id':'a','deps':['missing']}])
reject('order',nodes=[{'id':'a','deps':[]},{'id':'a','deps':[]}])
reject('order',nodes=[{'id':'a','deps':['b']},{'id':'b','deps':['a']}])
reject('order',nodes=[{'id':'a','deps':['a']}])
# Independent invariant check over all acyclic forward graphs of four nodes.
import itertools
names=['d','b','a','c']; pairs=[(a,b) for a in range(4) for b in range(a)]
for mask in range(1<<len(pairs)):
    deps={n:set() for n in names}
    for bit,(a,b) in enumerate(pairs):
        if mask & (1<<bit): deps[names[a]].add(names[b])
    nodes=[{'id':n,'deps':sorted(deps[n])} for n in reversed(names)]
    result=call('order',nodes=nodes);done=set()
    for chosen in result:
        eligible=[n['id'] for n in nodes if n['id'] not in done and deps[n['id']]<=done]
        assert chosen==eligible[0]
        done.add(chosen)
    assert done==set(names)
cli({'action':'order','nodes':[{'id':'a','deps':['b']},{'id':'b','deps':[]}]},['b','a'])
cli_error({'action':'order','nodes':[{'id':'a','deps':['x']}]})
