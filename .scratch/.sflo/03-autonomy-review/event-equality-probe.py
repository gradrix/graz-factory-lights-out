"""Supplemental semantic probes; never alters frozen cohort inputs or scores."""
import json
from pathlib import Path
import tempfile
from gflo.sandbox import Sandbox

repo = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
code = '''import json
from api import dispatch

def event(data, seq=1): return dict(source='a', seq=seq, data=data)
def check(name, events, conflict=False):
    try:
        result=dispatch(dict(action='ingest',watermarks={},events=events))
        ok=not conflict
        return dict(case=name,passed=ok,result=result)
    except ValueError as error:
        return dict(case=name,passed=conflict,error=str(error))
results=[check('equal-numeric-forms',[event(1),event(1.0)]),
         check('bool-distinct-from-number',[event(True),event(1)],True),
         check('large-distinct-integers',[event(10**20),event(10**20+1)],True),
         check('sparse-sequence',[event(None,10**9)])]
assert len(results[0].get('result',{}).get('released',[]))==1 or not results[0]['passed']
assert results[-1]['result']['pending']==[event(None,10**9)]
print(json.dumps(results))
'''
acceptance = repo / 'evaluations/coding-b/tasks/11-event-watermarks/acceptance'
results = {}
with tempfile.TemporaryDirectory(prefix='gflo-json-reference-') as directory:
    root = Path(directory)
    reference = json.loads((repo / 'evaluations/coding-b/private/references/11.json').read_text())
    for name, text in reference.items():
        (root/name).write_text(text)
    results['prepared_reference'] = Sandbox().execute(root, ['python','-B','-c',code], acceptance=acceptance, timeout=5)
    candidate = repo / '.gflo/semantic-b/c38088d51d73/workspace'
    if candidate.exists():
        results['frozen_candidate'] = Sandbox().execute(candidate, ['python','-B','-c',code], acceptance=acceptance, timeout=5)
results['interpretation'] = 'RFC6902 section4.6 JSON equality: same JSON type; numbers compared numerically. Supplemental interpretation probes; not frozen score changes.'
results['source'] = 'https://www.rfc-editor.org/rfc/rfc6902.txt'
(evidence / 'event-equality-probe.json').write_text(json.dumps(results,indent=2)+'\n')
for name,result in results.items():
    if isinstance(result,dict):print(name,result['exit_code'],result['output'])
