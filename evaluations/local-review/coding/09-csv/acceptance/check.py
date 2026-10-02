import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import parse, health
assert health()=={"status":"ok","version":1}
assert parse('name,value\n"a,b",3\n')==[('a,b',3)]
assert parse('name,value\n')==[]
assert parse('name,value\n"a\nb",-2\n"a""b",0\n')==[('a\nb',-2),('a"b',0)]

