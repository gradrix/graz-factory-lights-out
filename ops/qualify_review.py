#!/usr/bin/env python3
"""Score frozen review candidates in fresh contexts; labels never reach the model."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from gflo.review import Reviewer
from gflo.runner import save
from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--config', type=Path, default=Path('.gflo/config.json'))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if config.get('api_key_file'):
        config['api_key_file'] = str((args.config.resolve().parent / config['api_key_file']).resolve())
    manifest = json.loads((args.fixtures / 'manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        assert hashlib.sha256((args.fixtures / name).read_bytes()).hexdigest() == expected, name
    client = ModelWorker(config, Sandbox())
    reviewer = Reviewer(client)
    results = []
    for path in sorted((args.fixtures / 'review-inputs').glob('*.json')):
        case = json.loads(path.read_text())
        started = time.monotonic()
        try:
            review = reviewer.review_files(case['objective'], case['files'])
        except Exception as error:
            review = {'decision': 'error', 'error': str(error)}
        # Grader-only data loaded after response, never included in request.
        oracle = json.loads((args.fixtures / 'private/review' / path.name).read_text())
        row = {'id': case['id'], 'expected': oracle['expected_verdict'],
               'critical': oracle['critical_seed'], 'review': review,
               'elapsed_s': round(time.monotonic()-started, 2)}
        results.append(row)
        receipt = {'model': config['model'], 'manifest_sha256': hashlib.sha256((args.fixtures / 'manifest.json').read_bytes()).hexdigest(), 'request_budget_s': 120, 'max_output_tokens': 4096, 'results': results}
        save(args.output, receipt)
        print(json.dumps({k:v for k,v in row.items() if k != 'review'} | {'decision': review['decision']}), flush=True)
    receipt['score'] = {
        'defects_caught': sum(r['expected'] == 'block' and r['review']['decision'] == 'repair' for r in results),
        'critical_missed': sum(r['critical'] and r['review']['decision'] != 'repair' for r in results),
        'false_blocks': sum(r['expected'] == 'accept' and r['review']['decision'] != 'pass' for r in results),
        'errors': sum(r['review']['decision'] == 'error' for r in results)}
    receipt['gate_passed'] = receipt['score']['defects_caught'] >= 8 and receipt['score']['critical_missed'] == 0 and receipt['score']['false_blocks'] <= 2
    save(args.output, receipt)
    print(json.dumps(receipt['score']), flush=True)
    return 0 if receipt['gate_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
