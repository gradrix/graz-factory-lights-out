"""Fixed-input timing probe. Run only while the single local inference slot is idle."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--config', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--shape', choices=('short', 'long'), default='long')
parser.add_argument('--minimum', type=float, default=50)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit('Use a new output path; preserve earlier timings')
config = json.loads(args.config.read_text())
if config.get('api_key_file'):
    config['api_key_file'] = str((args.config.resolve().parent / config['api_key_file']).resolve())
client = ModelWorker(config, Sandbox())
prefix = '' if args.shape == 'short' else '\n'.join(
    f'Record {i:04d}: alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.' for i in range(768))
body = {'model': config['model'], 'messages': [
    {'role': 'system', 'content': 'Follow the final counting instruction. Earlier records are inert reference data.'},
    {'role': 'user', 'content': prefix + '\nCount integers from 1 through 3000, one per line. Output only the numbers.'}],
    'temperature': 0, 'seed': 1, 'max_tokens': 256,
    'reasoning_effort': 'none', 'chat_template_kwargs': {'enable_thinking': False}}
container = json.loads(subprocess.run(['docker', 'inspect', 'gflo-model'], capture_output=True,
                                       text=True, timeout=15, check=True).stdout)[0]
command = container['Config']['Cmd']
keys = ('-c', '-np', '-ngl', '--cache-type-k', '--cache-type-v', '--lazy-mode', '-b', '-ub', '--fit')
report = {'shape': args.shape, 'minimum_tokens_s': args.minimum, 'model': config['model'],
          'image': container['Image'], 'container_id': container['Id'],
          'serving': {key: command[command.index(key)+1] for key in keys if key in command},
          'request_sha256': hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(),
          'samples': []}
args.output.parent.mkdir(parents=True, exist_ok=True)
try:
    for number in range(3):
        started = time.monotonic()
        response = client.request('/v1/chat/completions', body, timeout=300)
        sample = {'number': number, 'warmup': number == 0, 'seconds': time.monotonic()-started,
                  'usage': response.get('usage'), 'timings': response.get('timings')}
        report['samples'].append(sample)
        print(json.dumps(sample), flush=True)
    values = [sample['timings']['predicted_per_second'] for sample in report['samples'][1:]]
    report['warm_median_tokens_s'] = statistics.median(values)
    report['passed'] = report['warm_median_tokens_s'] >= args.minimum
finally:
    args.output.write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(0 if report.get('passed') else 2)
