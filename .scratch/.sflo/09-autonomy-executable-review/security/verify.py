#!/usr/bin/env python3
"""Reproduce focused local security controls; no Docker or model calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
evidence = Path(__file__).resolve().parent
expected = {
    'ops/executable_review_prototype.py': 'ede30d388c75b1c69c683dbd4c61cae408afc73cd5d35f84c1748d0ab281ecaa',
    'ops/test_executable_review_security.py': '1b1f1868caf4511d81cb8703498cc3c8d79ac5bd0e0c7998f16e09dbc25e88db',
}
expected.update(json.loads((evidence.parent/'carry-forward.json').read_bytes())['source_sha256'])
def hashes():
    return {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in expected}
before = hashes()
assert before == expected, 'Frozen source or independent controls changed'
result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'ops', '-p',
                         'test_executable_review_security.py', '-v'], cwd=root,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
(evidence/'final-controls.txt').write_bytes(result.stdout)
after = hashes()
binding = {'outcome': 'PASS' if result.returncode == 0 and before == after else 'FAIL',
           'control_count': 18, 'returncode': result.returncode, 'source_before': before,
           'source_after': after, 'unchanged': before == after,
           'controls_sha256': hashlib.sha256(result.stdout).hexdigest(),
           'boundary': 'Fake HTTP/guardian, local files and signals only; no Docker/model/service operations'}
(evidence/'final-binding.json').write_text(json.dumps(binding, indent=2)+'\n')
print(json.dumps({key:value for key,value in binding.items() if key not in ('source_before','source_after')}, indent=2))
assert result.returncode == 0 and before == after
