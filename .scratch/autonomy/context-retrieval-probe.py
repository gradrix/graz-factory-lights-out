"""A bounded three-position retrieval check, not a coding-quality benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--config', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--records', type=int, default=3700)
a = p.parse_args()
if a.output.exists():
    raise ValueError('Preserve previous results; choose a fresh output path')
config = json.loads(a.config.read_text())
if config.get('api_key_file'):
    config['api_key_file'] = str((a.config.resolve().parent / config['api_key_file']).resolve())
client = ModelWorker(config, Sandbox())
def serving():
    item = json.loads(subprocess.run(['docker', 'inspect', 'gflo-model'], capture_output=True,
                                    text=True, timeout=15, check=True).stdout)[0]
    return {'container_id': item['Id'], 'image': item['Image'], 'command': item['Config']['Cmd']}
identity = serving()
expected = {'north': 'cobalt-7419', 'middle': 'cedar-2856', 'south': 'amber-9631'}
records = [f'Record {i:04d}: alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.' for i in range(a.records)]
for index, (name, value) in zip((3, a.records//2, a.records-4), expected.items()):
    records[index] = f'Authoritative lookup entry: {name} = {value}. Preserve the value exactly.'
body = {'model': config['model'], 'messages': [
    {'role': 'system', 'content': 'Read the records and return the requested lookup values. Output only a JSON object.'},
    {'role': 'user', 'content': '\n'.join(records) + '\nReturn north, middle and south lookup values as a JSON object.'}],
    'temperature': 0, 'seed': 1, 'max_tokens': 256, 'reasoning_effort': 'none',
    'chat_template_kwargs': {'enable_thinking': False}}
started = time.monotonic()
report = {'records': a.records, 'expected': expected,
          'serving': identity,
          'request_sha256': hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()}
try:
    response = client.request('/v1/chat/completions', body, timeout=300)
    assert serving() == identity, 'Serving identity changed during retrieval'
    content = response['choices'][0]['message']['content']
    report.update(response=content, usage=response.get('usage'), timings=response.get('timings'))
    try:
        report['passed'] = json.loads(content) == expected
    except (ValueError, TypeError):
        report['passed'] = False
finally:
    report['elapsed_s'] = time.monotonic()-started
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
raise SystemExit(0 if report.get('passed') else 2)
