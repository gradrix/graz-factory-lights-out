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

assert dispatch({'action': 'length', 'text': 'A😀é'}) == 4
cli({'action': 'length', 'text': 'A😀é'}, 4)
reject("not-an-action")
cli_error({"action":"not-an-action"})

assert call('index',text='A😀é',byte_offsets=[8,0,1,5,6,1])=={'byte_length':8,'char_to_byte':[0,1,5,6,8],'byte_to_char':[4,0,1,2,3,1]}
assert call('index',text='',byte_offsets=[0,0])=={'byte_length':0,'char_to_byte':[0],'byte_to_char':[0,0]}
for offset in [-1,2,3,4,7,9]:reject('index',text='A😀é',byte_offsets=[offset])
for value in ['abc','é','é','中😀','\x00a','👩\u200d💻']:
    encoded=value.encode('utf-8');boundaries=[]
    for n in range(len(encoded)+1):
        try:prefix=encoded[:n].decode('utf-8')
        except UnicodeDecodeError:continue
        boundaries.append((n,len(prefix)))
    r=call('index',text=value,byte_offsets=[n for n,_ in reversed(boundaries)])
    assert r['char_to_byte']==[n for n,_ in boundaries] and r['byte_to_char']==[i for _,i in reversed(boundaries)]
cli({'action':'index','text':'é','byte_offsets':[0,2]},{'byte_length':2,'char_to_byte':[0,2],'byte_to_char':[0,1]})
