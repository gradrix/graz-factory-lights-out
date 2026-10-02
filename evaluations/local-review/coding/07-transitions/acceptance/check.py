import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import transition, health
assert health()=={"status":"ok","version":1}
j={'status':'done'}
try: transition(j,'running')
except ValueError: pass
else: raise AssertionError('accepted')
assert j=={'status':'done'}
allowed={('queued','running'),('queued','cancelled'),('running','done'),('running','failed')}
for old in ['queued','running','done','failed','cancelled']:
    for new in ['queued','running','done','failed','cancelled']:
        j={'status':old}
        if (old,new) in allowed: assert transition(j,new)==new and j['status']==new
        else:
            try: transition(j,new)
            except ValueError: pass
            else: raise AssertionError((old,new))
            assert j['status']==old


