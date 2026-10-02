from pathlib import Path
import sys,json
base=Path(__file__).resolve().parent;
from qa_pinned import activate, evidence, RECHECK
activate(RECHECK)
from gflo.observe import Observer
from gflo.runner import Factory
from gflo.review import validate,load_files
root=evidence('qa-recheck-evidence')
f=Factory(root/'receipt',None,None); rid=f.status()[0]['id']; assert Observer(f.state).status(rid)['status']=='invalidated'
f=Factory(root/'valid',None,None); rid=f.status()[0]['id']; assert Observer(f.state).status(rid)['status']=='accepted'
review=f.state/rid/'attempts/1/review.json'; original=review.read_bytes(); review.write_text('{}')
assert f.status(rid)['status']=='invalidated'; assert Observer(f.state).status(rid)['status']=='invalidated'; review.write_bytes(original)
assert f.status(rid)['status']=='accepted'
valid={'decision':'repair','findings':[{'severity':'major','path':'app.py','line':1,'evidence':'wrong value','repair':'set correct value'}],'question':''}
assert validate(valid,{'app.py':'value=2\n'})==valid
for change in [dict(valid,question='Which value?'),dict(valid,findings=[dict(valid['findings'][0],path='absent.py')])]:
 try:validate(change,{'app.py':'value=2\n'})
 except ValueError:pass
 else:raise AssertionError(change)
large=root/'oversized'; large.mkdir(exist_ok=True); (large/'app.py').write_text('x'*200001)
try:load_files(large)
except ValueError:pass
else:raise AssertionError('oversized accepted')
print('PASS: Observer and Factory deletion/mutation parity; repair-question contradiction; invalid source; oversized files')
