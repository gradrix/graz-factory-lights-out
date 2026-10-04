"""Post-trial boundedness/backward-replay probes; no inference or product writes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('.gflo/document-citation-prototype').resolve()
sys.argv = ['prototype.py', str(ROOT)]
spec = importlib.util.spec_from_file_location('prototype', ROOT / 'prototype.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
from gflo.documents import DocumentStore, encoded

findings = {}
evidence = json.loads((ROOT / 'inputs/csv.json').read_text())
base = {'status': 'supported', 'claims': [{'text': 'Test claim', 'citations': [
    {'evidence_id': evidence['id'], 'span': 1}]}], 'reason': ''}
boundaries = []
for text, expected in [('a' * 4096, True), ('a' * 4097, False), ('é' * 2048, True), ('é' * 2049, False)]:
    example = dict(evidence, spans=[text])
    try:
        answer = p.refs(base, example)
        passed = True
        assert answer['claims'][0]['citations'][0]['excerpt'] == text
    except ValueError:
        passed = False
    assert passed == expected
    boundaries.append({'utf8_bytes': len(text.encode()), 'character_count': len(text), 'accepted': passed})
findings['whole_span_boundaries'] = boundaries
many = {'status': 'supported', 'claims': [
    {'text': 'Test claim', 'citations': [dict(base['claims'][0]['citations'][0]) for _ in range(8)]}
    for _ in range(16)], 'reason': ''}
derived = p.refs(many, dict(evidence, spans=['a' * 4096]))
findings['legal_reference_expansion'] = {'model_json_bytes': len(encoded(many)),
    'derived_answer_bytes': len(encoded(derived)), 'existing_receipt_limit_bytes': 65536,
    'answer_alone_exceeds_receipt_limit': len(encoded(derived)) > 65536}
rows = json.loads((ROOT / 'results/results.json').read_text())
sizes = []
for row in rows:
    attempts = ROOT / 'results' / row['case'] / row['method']
    raw_calls = []
    for attempt in row['attempts']:
        path = attempts / str(attempt['attempt'])
        response = json.loads((path / 'response.raw.json').read_bytes())
        assert response == json.loads((path / 'response.json').read_text())
        message = response['choices'][0]['message']
        assert not message.get('tool_calls') and not message.get('function_call')
        raw_calls.append(response)
    sizes.append({'case': row['case'], 'method': row['method'],
                  'derived_answer_bytes': len(encoded(row['answer'])),
                  'raw_responses_plus_answer_bytes': len(encoded({'responses': raw_calls, 'answer': row['answer']}))})
findings['observed_sizes'] = sizes
# Isolate accepted cache copy; the original saved receipts are never rewritten.
destination = ROOT / 'offline-replay-store'
shutil.copytree('.gflo/document-research-cohort/csv/store', destination)
destination.chmod(0o700)
store = DocumentStore(destination, executor=lambda *a, **k: (_ for _ in ()).throw(AssertionError('Executor forbidden')))
old = []
for directory in destination.iterdir():
    if not directory.is_dir():
        continue
    receipt_path = directory / 'receipt.json'
    receipt = json.loads(receipt_path.read_bytes())
    if receipt['kind'] == 'answer':
        before = receipt_path.read_bytes()
        value = store.replay(directory.name)
        assert before == receipt_path.read_bytes()
        old.append({'id': directory.name, 'receipt_sha256': hashlib.sha256(before).hexdigest(), 'status': value['answer']['status']})
findings['unchanged_accepted_replay'] = old
assert old
compatibility = []
for row in rows:
    if row['method'] == 'references' and row['case'] != 'skipkeys':
        replay = store._replay({'id': 'prototype-only-not-published', 'receipt': {
            'kind': 'answer', 'evidence_id': evidence['id'], 'answer': row['answer'],
            'verdict': 'citation_provenance_valid_not_semantic_entailment'}})
        assert replay['answer'] == row['answer']
        compatibility.append(row['case'])
findings['derived_answer_existing_replay_shape'] = compatibility
target = Path('.scratch/autonomy/document-citation-prototype/offline-analysis.json')
target.write_text(json.dumps(findings, indent=2) + '\n')
print(json.dumps(findings, indent=2))
