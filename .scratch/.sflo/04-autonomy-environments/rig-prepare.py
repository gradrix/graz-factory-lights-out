"""Cold package-cache qualification driver; run inside the frozen rig checkout."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
report = {'candidate': '51479e9', 'source': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(Path('gflo').rglob('*')) if p.is_file() and '__pycache__' not in str(p)},
          'profiles': []}
output = root / '.gflo/stage3-preparation'
output.mkdir(parents=True, exist_ok=True)
store = output / 'environments'
if store.exists():
    raise SystemExit('Cold qualification requires an unused environment store')
try:
    for profile in ('python-stdlib', 'python-api', 'node-ts'):
        started = time.monotonic()
        command = [sys.executable, '-m', 'gflo', 'environment', '--store', str(store), 'prepare', profile]
        result = subprocess.run(command, capture_output=True, text=True, timeout=270)
        (output / (profile + '.stdout')).write_text(result.stdout)
        (output / (profile + '.stderr')).write_text(result.stderr)
        row = {'profile': profile, 'exit_code': result.returncode, 'seconds': time.monotonic()-started}
        report['profiles'].append(row)
        if result.returncode:
            raise RuntimeError(profile + ' preparation failed: ' + result.stderr)
        prepared = json.loads(result.stdout)
        row.update(prepared)
        receipt = store / prepared['id'] / 'receipt.json'
        row['receipt'] = json.loads(receipt.read_text())
        checked = subprocess.run([sys.executable, '-m', 'gflo', 'environment', '--store', str(store),
                                  'check', prepared['id'], '--repeat', '2'], capture_output=True, text=True, timeout=180)
        row['check_exit_code'] = checked.returncode
        row['checks'] = json.loads(checked.stdout) if checked.returncode == 0 else checked.stderr
        if checked.returncode:
            raise RuntimeError(profile + ' offline check failed')
        print(json.dumps({'profile': profile, 'id': prepared['id'], 'prepared': True, 'offline_checks': 2}), flush=True)
finally:
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
