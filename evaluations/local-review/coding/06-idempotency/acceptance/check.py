import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import apply, health
assert health()=={"status":"ok","version":1}
s={'balance':10,'seen':{}}
assert apply(s,'a',0)==10
try: apply(s,'a',7)
except ValueError: pass
else: raise AssertionError('conflict accepted')
assert s=={'balance':10,'seen':{'a':0}}
s={'balance':0,'seen':{}}
assert apply(s,'x',5)==5
assert apply(s,'y',2)==7
assert apply(s,'x',5)==7
assert s=={'balance':7,'seen':{'x':5,'y':2}}

