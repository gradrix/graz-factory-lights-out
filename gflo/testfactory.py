"""Build a test-writing task: the worker writes tests, acceptance is mechanical (see recipes/test_acceptance.py)."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

RECIPE = Path(__file__).parent / 'recipes' / 'test_acceptance.py'
OBJECTIVE = ('Write focused, meaningful pytest tests for {targets}. Put them in new or existing test_*.py modules under '
             'tests/. Do not modify any non-test file. The tests must pass reliably on the current code and must fail '
             'when the behaviour of the target changes: acceptance mutates {targets} (flipped comparisons and '
             'operators, changed constants, removed negations, returns replaced by None) and requires your new tests '
             'to detect at least {percent}% of those mutants. Cover normal behaviour, boundaries and error paths through '
             'the public interface; every test needs real assertions, and trivial or tautological tests are rejected. '
             'If a target behaviour looks like a bug, test the current behaviour and mention it in your summary.')


def tracked(repo):
    names = subprocess.run(['git', '-C', str(repo), 'ls-files', '*.py'], check=True, capture_output=True, text=True).stdout
    return [name for name in names.splitlines() if name]


def build(repo, targets, out, *, threshold=0.6, max_mutants=30, runs=3, profile='python-project',
          runner=None, checks_env=()):
    """Write OUT/task.json and OUT/acceptance for tests of TARGETS in the clean git repository REPO."""
    spec = importlib.util.spec_from_file_location('test_acceptance', RECIPE)
    acceptance_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acceptance_module)
    if runner is None:  # the stdlib profile has no pytest; unittest also accepts test file paths
        runner = (('python', '-m', 'unittest', '{tests}') if profile == 'python-stdlib'
                  else ('python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-x', '{tests}'))
    repo, out = Path(repo).resolve(), Path(out).resolve()
    if subprocess.run(['git', '-C', str(repo), 'status', '--porcelain'], check=True, capture_output=True, text=True).stdout.strip():
        raise ValueError('Repository must be clean; commit the intended base first')
    files = tracked(repo)
    for target in targets:
        if target not in files or acceptance_module.is_test(target):
            raise ValueError(f'Target must be a tracked non-test Python file: {target}')
        if not acceptance_module.mutation_sites(ast.parse((repo / target).read_text())):
            raise ValueError(f'Target has no mutable code: {target}')
    digest = lambda name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
    config = {'targets': list(targets), 'threshold': threshold, 'max_mutants': max_mutants, 'runs': runs,
              'runner': [*checks_env, *runner],
              'base': {name: digest(name) for name in files if not acceptance_module.is_test(name)},
              'base_tests': {name: digest(name) for name in files if acceptance_module.is_test(name)}}
    acceptance = out / 'acceptance'
    acceptance.mkdir(parents=True, exist_ok=False)
    shutil.copy2(RECIPE, acceptance / 'test_acceptance.py')
    (acceptance / 'test_task.json').write_text(json.dumps(config, indent=1) + '\n')
    check = ['python', '/acceptance/test_acceptance.py']
    task = {'repo': str(repo), 'acceptance': 'acceptance', 'profile': profile, 'checks': [check], 'test_command': check,
            'objective': OBJECTIVE.format(targets=', '.join(targets), percent=round(threshold * 100)),
            'max_attempts': 3, 'max_turns': 40}
    (out / 'task.json').write_text(json.dumps(task, indent=1) + '\n')
    return out / 'task.json'
