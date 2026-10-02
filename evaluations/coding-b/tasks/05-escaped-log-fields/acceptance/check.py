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

assert dispatch({'action': 'field_names', 'fields': {'z': '1', 'a': '2'}}) == ['a', 'z']
cli({'action': 'field_names', 'fields': {'z': '1', 'a': '2'}}, ['a', 'z'])
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('encode',fields={'b':'x=y','a':'one\ntwo\t\\\r'})=='a=one\\ntwo\\t\\\\\\r\tb=x=y'
assert call('decode',line='b=x=y\ta=')=={'a':'','b':'x=y'}
assert call('encode',fields={})==''
assert call('decode',line='')=={}
for line in ['a=1\ta=2','a=1\t','noequals','=x','bad-key=x','a=\\q','a=\\']:
    reject('decode',line=line)
reject('encode',fields={'9bad':'x'})
import itertools
for chars in itertools.product(['x','=','\t','\n','\r','\\','é'],repeat=3):
    value=''.join(chars)
    assert call('decode',line=call('encode',fields={'value':value}))=={'value':value}
cli({'action':'decode','line':'a=one\\ntwo\tb=x=y'},{'a':'one\ntwo','b':'x=y'})
