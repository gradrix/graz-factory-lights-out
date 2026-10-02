import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import coalesce, health
assert health()=={"status":"ok","version":1}
x=[(4,7),(1,3),(3,5),(10,11)]
assert coalesce(x)==[(1,7),(10,11)]
assert x==[(4,7),(1,3),(3,5),(10,11)]
assert coalesce([])==[]
assert coalesce([(1,8),(2,3),(-2,0),(0,1)])==[(-2,8)]
assert coalesce([(1,2),(4,5)])==[(1,2),(4,5)]

