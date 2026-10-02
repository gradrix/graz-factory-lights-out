import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import lines, health
assert health()=={"status":"ok","version":1}
assert lines(['ab','c\r','\n\n','tail\r'])==['abc','','tail\r']
assert lines([])==[]
assert lines(['a\n'])==['a']
assert lines(['','\n','','\n'])==['','']
assert lines(['a\r\rb\n'])==['a\r\rb']
assert lines(['a\r\r\n'])==['a\r']

