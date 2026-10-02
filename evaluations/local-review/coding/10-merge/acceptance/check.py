import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import merge, health
assert health()=={"status":"ok","version":1}
a={'x':{'a':1},'l':[1]}; b={'x':{'b':2}}
r=merge(a,b)
assert a=={'x':{'a':1},'l':[1]}
r['l'].append(2)
assert a['l']==[1]
a={'d':{'x':1},'n':2};b={'d':{'y':[3]},'n':{'v':4}}
r=merge(a,b)
assert r=={'d':{'x':1,'y':[3]},'n':{'v':4}}
r['d']['y'].append(9)
r['n']['v']=5
assert b=={'d':{'y':[3]},'n':{'v':4}}

