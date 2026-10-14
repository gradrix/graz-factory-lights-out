"""Acceptance for generated objective checks, run in the sandbox as /acceptance/check.py (decision 015 prototype).

The workspace is the unmodified base plus the checks. It passes when the only new files are
tests/objective_checks/test_*.py (and an __init__.py), there are at least MIN_TESTS test functions,
they collect, and every one fails: a check that passes before the change is made cannot tell whether it was.
Pytest arguments after the script name are passed through (for example -p no:cacheprovider).
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ElementTree

CHECKS = 'tests/objective_checks'
ALLOWED = re.compile(r'tests/objective_checks/(test_[A-Za-z0-9_]+|__init__)\.py')
SKIP = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.hypothesis'}
MIN_TESTS = 3


def files(root):
    root = Path(root)
    found = {}
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if any(part in SKIP for part in relative.parts) or path.suffix == '.pyc' or not path.is_file():
            continue
        found[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def layout_problems(workspace, base):
    """Base files must be unchanged; new files only checks modules. Returns (problems, check files)."""
    now = files(workspace)
    problems = [f'base file changed or removed: {name}' for name in sorted(base) if now.get(name) != base[name]]
    added = sorted(set(now) - set(base))
    problems += [f'new file outside {CHECKS}/test_*.py: {name}' for name in added if not ALLOWED.fullmatch(name)]
    return problems, [name for name in added if ALLOWED.fullmatch(name)]


def count_tests(workspace, names):
    total = 0
    for name in names:
        tree = ast.parse((Path(workspace) / name).read_text())
        total += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test')
                     for node in ast.walk(tree))
    return total


def main(workspace='/workspace', acceptance='/acceptance'):
    base = json.loads((Path(acceptance) / 'base_files.json').read_text())
    problems, checks = layout_problems(workspace, base)
    if not problems and count_tests(workspace, checks) < MIN_TESTS:
        problems.append(f'fewer than {MIN_TESTS} test functions in {CHECKS}/test_*.py')
    if problems:
        print('\n'.join(problems))
        return 1
    report = Path('/tmp/objective-checks.xml')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', *sys.argv[1:], f'--junitxml={report}', CHECKS],
                            cwd=workspace, capture_output=True, text=True)
    cases = list(ElementTree.parse(report).iter('testcase')) if report.exists() else []
    if result.returncode in (2, 3, 4, 5) or not cases:
        print('the checks do not collect or run:\n' + (result.stdout + result.stderr)[-3000:])
        return 1
    passing = [case.get('name') for case in cases if not any(child.tag in ('failure', 'error', 'skipped') for child in case)]
    skipped = [case.get('name') for case in cases if any(child.tag == 'skipped' for child in case)]
    if passing or skipped:
        if passing:
            print('these checks pass on the unmodified code, so they cannot tell whether the change was made: ' + ', '.join(passing))
        if skipped:
            print('skipped checks are not allowed: ' + ', '.join(skipped))
        return 1
    print(f'{len(cases)} checks, all failing on the unmodified code as required')
    return 0


if __name__ == '__main__':
    sys.exit(main())
