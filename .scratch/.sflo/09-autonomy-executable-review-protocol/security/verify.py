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
    'ops/executable_review_prototype.py': 'c69e90f8359603b9bf6636fa02a6b0887a4ba2af38f9f481243f9c8e831530a8',
    'ops/test_executable_review_security.py': '8f9fbd7ec791bf9f08a8cf929a88fe5b1f4b060b40b08787006791af47c4b612',
}
expected.update(json.loads((evidence.parent/'carry-forward.json').read_bytes())['reused_source_sha256'])
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
           'control_count': 41, 'returncode': result.returncode, 'source_before': before,
           'source_after': after, 'unchanged': before == after,
           'controls_sha256': hashlib.sha256(result.stdout).hexdigest(),
           'boundary': 'Fake HTTP/guardian, local files and signals only; no Docker/model/service operations'}
(evidence/'final-binding.json').write_text(json.dumps(binding, indent=2)+'\n')
print(json.dumps({key:value for key,value in binding.items() if key not in ('source_before','source_after')}, indent=2))
assert result.returncode == 0 and before == after
