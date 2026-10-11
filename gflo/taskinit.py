"""Build a change task for an existing Python project without writing acceptance checks.

Acceptance is the one measured on real repositories (roadmap phase 1): the project's own pytest suite may not gain
failures over the base commit (recipes/suite_acceptance.py), plus the factory's usual regression-test discovery and
review. The base suite runs once here, offline in the sandbox, to record what already fails.
"""
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ElementTree

RECIPE = Path(__file__).parent / 'recipes' / 'suite_acceptance.py'
PYTEST = ['python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider']
FOOTER = ('\n\nHow to run tests in this project: {targeted} (narrow it to one test file while working). Acceptance (check) runs the '
          'whole suite and rejects only new failures; {failing} tests already fail on the base commit.')


def base_outcomes(sandbox, repo, command, timeout):
    """Per-test outcomes of COMMAND on a copy of REPO's HEAD; True means passed."""
    with tempfile.TemporaryDirectory(prefix='gflo-base-') as directory:
        workspace = Path(directory) / 'workspace'
        workspace.mkdir()
        archive = subprocess.run(['git', '-C', str(repo), 'archive', 'HEAD'], check=True, capture_output=True).stdout
        subprocess.run(['tar', '-x', '-C', str(workspace)], input=archive, check=True)
        report = workspace / '.gflo-junit.xml'
        try:
            result = sandbox.execute(workspace, [*command, '--junitxml=/workspace/.gflo-junit.xml'], timeout=timeout)
        finally:
            sandbox.cleanup(workspace)
        if not report.exists():
            raise ValueError('The test command produced no report on the base commit; check --pytest-args and --env. '
                             'Output tail: ' + (result.get('output') or '')[-1500:])
        return {case.get('classname', '') + '::' + case.get('name', ''):
                not any(child.tag in ('failure', 'error', 'skipped') for child in case)
                for case in ElementTree.parse(report).iter('testcase')}


def build(repo, objective, out, sandbox, *, pytest_args='tests', env=(), timeout=1500, max_attempts=3, max_turns=40):
    """Write OUT/task.json and OUT/acceptance; SANDBOX must be bound to the project's prepared environment."""
    repo, out = Path(repo).resolve(), Path(out).resolve()
    if not objective.strip():
        raise ValueError('Objective is empty; describe the required behaviour and the public interfaces involved')
    if subprocess.run(['git', '-C', str(repo), 'status', '--porcelain'], check=True, capture_output=True, text=True).stdout.strip():
        raise ValueError('Repository must be clean; commit the intended base first')
    prefix = ['env', *env] if env else []
    arguments = shlex.split(pytest_args)
    outcomes = base_outcomes(sandbox, repo, [*prefix, *PYTEST, *arguments], timeout)
    if not any(outcomes.values()):
        raise ValueError(f'No test passes on the base commit ({len(outcomes)} collected); acceptance needs a working suite')
    failing = sorted(key for key, passed in outcomes.items() if not passed)
    acceptance = out / 'acceptance'
    acceptance.mkdir(parents=True, exist_ok=False)
    shutil.copy2(RECIPE, acceptance / 'check.py')
    (acceptance / 'baseline_failures.json').write_text(json.dumps(failing, indent=1) + '\n')
    check = [*prefix, 'python', '/acceptance/check.py', *PYTEST[3:], *arguments]
    targeted = shlex.join([*prefix, *PYTEST, *arguments])
    task = {'repo': str(repo), 'acceptance': 'acceptance', 'profile': 'python-project',
            'objective': objective.strip() + FOOTER.format(targeted=targeted, failing=len(failing)),
            'checks': [check], 'test_command': check, 'max_attempts': max_attempts, 'max_turns': max_turns}
    (out / 'task.json').write_text(json.dumps(task, indent=1) + '\n')
    return {'task': str(out / 'task.json'), 'tests': len(outcomes), 'failing_on_base': len(failing)}
