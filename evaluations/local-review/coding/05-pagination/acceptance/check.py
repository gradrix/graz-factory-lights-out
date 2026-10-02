import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import collect, health
assert health()=={"status":"ok","version":1}
pages={None:{'items':[1],'next':'a'},'a':{'items':[],'next':'b'},'b':{'items':[2],'next':None}}
assert collect(pages.__getitem__)==[1,2]
assert collect(lambda cursor: {'items':[], 'next':None})==[]
pages={None:{'items':[],'next':''},'':{'items':[4,3],'next':None}}
assert collect(pages.__getitem__)==[4,3]

