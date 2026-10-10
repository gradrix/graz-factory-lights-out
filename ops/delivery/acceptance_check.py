"""Acceptance for a mined task: the project suite may not gain failures over the base commit.

Runs inside the verification sandbox: python /acceptance/check.py PYTEST_ARGS...
/acceptance/baseline_failures.json lists tests already failing on the base commit (for example
database tests the project does not mark); every other collected test must pass.
"""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ElementTree

allowed = set(json.loads(Path('/acceptance/baseline_failures.json').read_text()))
report = Path('/tmp/acceptance-junit.xml')
completed = subprocess.run([sys.executable, '-m', 'pytest', *sys.argv[1:], f'--junitxml={report}'],
                           capture_output=True, text=True)
if not report.exists():
    print(completed.stdout[-3000:], completed.stderr[-2000:])
    sys.exit('pytest produced no report (collection or configuration failure)')
failed, passed = [], 0
for case in ElementTree.parse(report).iter('testcase'):
    key = case.get('classname', '') + '::' + case.get('name', '')
    if any(child.tag in ('failure', 'error') for child in case):
        if key not in allowed:
            failed.append(key)
    elif not any(child.tag == 'skipped' for child in case):
        passed += 1
print(f'{passed} passed; {len(allowed)} pre-existing failures tolerated; {len(failed)} new failures')
for key in failed[:40]:
    print('NEW FAILURE', key)
sys.exit(1 if failed or passed == 0 else 0)
