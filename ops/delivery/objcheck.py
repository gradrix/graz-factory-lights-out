"""Objective-derived checks prototype (decision 015): generate checks from an objective alone, score them on known trees (rig).

  objcheck.py build SOURCE_TASKS OUT COMMIT...   # one generator task per commit from SOURCE_TASKS/<commit>
  objcheck.py evaluate CASES STORE OUT_JSONL     # run each case's generated checks on its trees

A generator task starts from the same base repository and environment as the delivery task. Its worker sees the
objective, never the reference change or a delivered patch, and writes tests/objective_checks/ under
ops/delivery/objective_check.py acceptance. CASES is a JSON list of {"key", "checks": <generator workspace>,
"environment", "test_command", "trees": {label: path}}; every tree is scored by which checks pass on it.
"""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.delivery.env_exec import execute  # noqa: E402
from ops.delivery.objective_check import CHECKS, files  # noqa: E402

FOOTER = '\n\nHow to run tests in this project:'
PROMPT = """Write acceptance checks for a change that has NOT been made yet. Another developer will implement the change \
described below in this repository; your checks decide whether their implementation is accepted.

Rules:
- Add pytest test functions only in new files {checks}/test_*.py. Do not change or add any other file.
- Check the concrete, observable requirements the description states: names, signatures, return values, exact strings \
and its worked examples. Cover every numbered item; one requirement per test where practical.
- Test only what the description states or what directly follows from it, never implementation details it leaves open.
- Every check must fail on the current code, because the change is not made yet. Never make a check pass by testing \
current behaviour.
- Import modules or names the change adds inside each test function, not at module top level, so a missing name fails \
only that test.
- Learn from the existing tests and code how to build inputs (fixtures, factories, sample data).
- Run your checks with: {run}
Acceptance (check) verifies these rules.

The change to check:

{objective}"""


def pytest_prefix(test_command):
    """The task's test command up to and including python, and its pytest options without the trailing path."""
    python = test_command.index('python')
    options = test_command[python + 2:-1]  # after "python <script or -m pytest>"
    if test_command[python + 1] == '-m':
        options = test_command[python + 3:-1]
    return test_command[:python], options


def build(source, out, commits):
    built = []
    for commit in commits:
        task = json.loads((Path(source) / commit / 'task.json').read_text())
        root = Path(out) / commit
        if (root / 'task.json').exists():
            built.append(commit)
            continue
        if root.exists():
            shutil.rmtree(root)
        shutil.copytree(Path(source) / commit / 'repo', root / 'repo', symlinks=True)
        shutil.copy2(Path(source) / commit / 'environment.txt', root / 'environment.txt')
        (root / 'acceptance').mkdir()
        shutil.copy2(Path(__file__).with_name('objective_check.py'), root / 'acceptance' / 'check.py')
        (root / 'acceptance' / 'base_files.json').write_text(json.dumps(files(root / 'repo')) + '\n')
        env, options = pytest_prefix(task['test_command'])
        check = env + ['python', '/acceptance/check.py'] + options
        run = ' '.join(env + ['python', '-m', 'pytest'] + [f"'{o}'" if ' ' in o else o for o in options] + [CHECKS])
        objective = task['objective'].split(FOOTER)[0]
        (root / 'task.json').write_text(json.dumps({
            'repo': 'repo', 'acceptance': 'acceptance', 'profile': task.get('profile', 'python-project'),
            'objective': PROMPT.format(checks=CHECKS, run=run, objective=objective),
            'checks': [check], 'test_command': check, 'max_attempts': 2, 'max_turns': 40}, indent=1) + '\n')
        built.append(commit)
    return built


def outcomes(store, environment, tree, checks, test_command, work):
    """{test name: passed} for the checks run on a copy of TREE."""
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(tree, work, symlinks=True, ignore=lambda d, names: ['.git'] if Path(d) == Path(tree) else [])
    if (work / CHECKS).exists():
        shutil.rmtree(work / CHECKS)
    shutil.copytree(Path(checks) / CHECKS, work / CHECKS)
    env, options = pytest_prefix(test_command)
    report = work / '.objective-checks.xml'
    result = execute(store, environment, work, env + ['python', '-m', 'pytest', '-q', *options,
                                                      '--junitxml=/workspace/.objective-checks.xml', CHECKS], timeout=1500)
    seen = {}
    if report.exists():
        for case in ElementTree.parse(report).iter('testcase'):
            seen[case.get('classname', '') + '::' + case.get('name', '')] = not any(
                child.tag in ('failure', 'error', 'skipped') for child in case)
    shutil.rmtree(work)
    return seen, result['output'][-800:]


def evaluate(cases, store, out):
    done = set()
    if Path(out).exists():
        done = {(row['key'], row['tree']) for row in map(json.loads, Path(out).read_text().splitlines())}
    for case in json.loads(Path(cases).read_text()):
        for label, tree in case['trees'].items():
            if (case['key'], label) in done:
                continue
            seen, tail = outcomes(store, case['environment'], tree, case['checks'], case['test_command'],
                                  Path(out).parent / 'objcheck-work')
            row = {'key': case['key'], 'tree': label, 'total': len(seen), 'passed': sum(seen.values()),
                   'failed': sorted(name for name, ok in seen.items() if not ok), 'tail': '' if seen else tail}
            with open(out, 'a') as stream:
                print(json.dumps(row), file=stream, flush=True)
            print(case['key'], label, f"{row['passed']}/{row['total']}", flush=True)


if __name__ == '__main__':
    if sys.argv[1:2] == ['build']:
        print(json.dumps(build(sys.argv[2], sys.argv[3], sys.argv[4:])))
    elif sys.argv[1:2] == ['evaluate']:
        evaluate(*sys.argv[2:5])
    else:
        raise SystemExit(__doc__)
