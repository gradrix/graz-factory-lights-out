import json,sys
from pathlib import Path
base=Path(__file__).resolve().parent

from qa_pinned import activate, evidence, RECHECK
activate(RECHECK)
from gflo.runner import Factory
rows=json.loads((base/'qa-recheck-evidence/results.json').read_text())
control=next(r for r in rows if r['name']=='blocking-pass')
assert control['actual']==control['expected']
control=next(r for r in rows if r['name']=='valid')
assert control['actual']==control['expected']
f=Factory(base/'qa-recheck-evidence/receipt',None,None)
rid=f.status()[0]['id']
(f.state/rid/'attempts/1/verification.json').unlink(missing_ok=True)
receipt=dict(name='all-review-evidence-missing',expected='invalidated',actual=f.status(rid)['status'])
rows.append(receipt)
(base/'qa-recheck-evidence/assertions.json').write_text(json.dumps(rows,indent=2))
failures=[r for r in rows if 'expected' in r and r['expected']!=r['actual']]
print(json.dumps(failures,indent=2))
sys.exit(bool(failures))
