import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import reserve, health
assert health()=={"status":"ok","version":1}
s={'a':5,'b':1}
assert reserve(s,[('a',2),('b',2)]) is False and s=={'a':5,'b':1}
assert reserve(s,[('a',2),('a',3)]) is True and s=={'a':0,'b':1}

s={'a':5}
assert reserve(s,[('missing',1)]) is False and s=={'a':5}
assert reserve(s,[('a',3),('a',3)]) is False and s=={'a':5}
for invalid in [0,-1,1.5,True]:
    try: reserve(s,[('a',1),('a',invalid)])
    except ValueError: pass
    else: raise AssertionError('invalid quantity accepted')
    assert s=={'a':5}
assert reserve(s,[]) is True


