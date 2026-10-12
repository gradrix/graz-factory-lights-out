"""Run all pilot cases serially on the rig; retain failures and wall time."""
import json
import logging
from pathlib import Path
import time
from gflo.runner import Factory, save
from gflo.worker import ModelWorker
from gflo.sandbox import Sandbox

logging.basicConfig(level=logging.INFO, format='%(message)s')
root = Path.cwd()
config = json.loads((root / '.gflo/config.json').read_text())
sandbox = Sandbox(config['image'])
worker = ModelWorker(config, sandbox)
factory = Factory(root / '.gflo/runs', worker, sandbox.verify, cleanup=sandbox.cleanup)
results = []
for name in ('invoice', 'inventory'):
    started = time.monotonic()
    run_id = factory.create(root / '.gflo/review-repairs' / name / 'task.json')
    print('START ' + name + ' ' + run_id, flush=True)
    try:
        result = factory.resume(run_id)
    except Exception as error:
        result = factory.status(run_id)
        result['error'] = str(error)
    result.update(scenario=name, elapsed_s=time.monotonic() - started)
    results.append(result)
    save(root / '.gflo/repair-summary.json', results)
    print('RESULT ' + json.dumps(result), flush=True)
raise SystemExit(0 if all(r['status'] == 'accepted' for r in results) else 2)
