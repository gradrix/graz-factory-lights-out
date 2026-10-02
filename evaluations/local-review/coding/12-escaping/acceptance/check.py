import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import render, health
assert health()=={"status":"ok","version":1}
assert render('<p>{x} {missing}</p>',{'x':'<&"'})=='<p>&lt;&amp;&quot; {missing}</p>'
assert render('{x}',{'x':'{y}','y':'oops'})=='{y}'

assert render('{a_b2} {a-b} {}',{'a_b2':42})=='42 {a-b} {}'
assert render('{q}',{'q':"'"})=='&#x27;'
assert render('plain',{})=='plain'

