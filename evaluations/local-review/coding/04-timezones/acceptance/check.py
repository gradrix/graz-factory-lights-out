import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import due, health
assert health()=={"status":"ok","version":1}
assert due([{'id':'x','at':'2026-01-01T12:00:00+02:00'}],'2026-01-01T10:30:00+00:00')==['x']
assert due([{'id':'y','at':'2026-01-01T09:00:00-02:00'}],'2026-01-01T10:30:00+00:00')==[]
assert due([{'id':1,'at':'2026-01-02T00:30:00+02:00'},{'id':2,'at':'2026-01-01T22:30:00+00:00'}],'2026-01-01T22:30:00+00:00')==[1,2]
assert due([],'2026-01-01T00:00:00+00:00')==[]

