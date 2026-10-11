"""Build a change task for an existing Python project without writing acceptance checks.

Acceptance is the one measured on real repositories (roadmap phase 1): the project's own pytest suite may not gain
failures over the base commit (recipes/suite_acceptance.py), plus the factory's usual review. The base suite runs
once here, offline in the sandbox, to record what already fails or is skipped.
"""
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ElementTree

RECIPE = Path(__file__).parent / 'recipes' / 'suite_acceptance.py'
PYTEST = ['python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider']
CHECK_SECONDS = 900  # sandbox.verify's per-check limit for python-project; the base run must leave room for changes
FOOTER = ('\n\nHow to run tests in this project: {targeted} (narrow it to one test file while working). Acceptance (check) runs the '
          'whole suite and rejects only new failures; tests already failing on the base commit: {failing}.')


def base_outcomes(sandbox, repo, command, clock=time.monotonic):
    """Per-test outcome ('passed', 'failed' or 'skipped') of COMMAND on a copy of REPO's HEAD, and its duration."""
    with tempfile.TemporaryDirectory(prefix='gflo-base-') as directory:
        workspace = Path(directory) / 'workspace'
        workspace.mkdir()
        archive = subprocess.run(['git', '-C', str(repo), 'archive', 'HEAD'], check=True, capture_output=True).stdout
        subprocess.run(['tar', '-x', '-C', str(workspace)], input=archive, check=True)
        report = workspace / '.gflo-junit.xml'
        started = clock()
        try:
            result = sandbox.execute(workspace, [*command, '--junitxml=/workspace/.gflo-junit.xml'], timeout=CHECK_SECONDS)
        finally:
            sandbox.cleanup(workspace)
        seconds = clock() - started
        if not report.exists():
            reason = f'timed out after {CHECK_SECONDS} s' if result.get('timed_out') else 'produced no report'
            raise ValueError(f'The test command {reason} on the base commit; check --pytest-args and --env. '
                             'Output tail: ' + (result.get('output') or '')[-1500:])
        outcomes = {}
        for case in ElementTree.parse(report).iter('testcase'):
            tags = {child.tag for child in case}
            outcomes[case.get('classname', '') + '::' + case.get('name', '')] = (
                'failed' if tags & {'failure', 'error'} else 'skipped' if 'skipped' in tags else 'passed')
        return outcomes, seconds


def build(repo, objective, out, sandbox, *, pytest_args='tests', env=(), max_attempts=3, max_turns=40, clock=time.monotonic):
    """Write OUT/task.json and OUT/acceptance; SANDBOX must be bound to the project's prepared environment."""
    repo, out = Path(repo).resolve(), Path(out).resolve()
    if not objective.strip():
        raise ValueError('Objective is empty; describe the required behaviour and the public interfaces involved')
    if out.exists():
        raise ValueError(f'{out} already exists; choose a new task directory')
    if any('=' not in item or item.startswith('=') for item in env):
        raise ValueError('--env values must look like NAME=VALUE')
    if subprocess.run(['git', '-C', str(repo), 'status', '--porcelain'], check=True, capture_output=True, text=True).stdout.strip():
        raise ValueError('Repository must be clean; commit the intended base first')
    prefix = ['env', *env] if env else []
    arguments = shlex.split(pytest_args)
    outcomes, seconds = base_outcomes(sandbox, repo, [*prefix, *PYTEST, *arguments], clock)
    if 'passed' not in outcomes.values():
        raise ValueError(f'No test passes on the base commit ({len(outcomes)} collected); acceptance needs a working suite')
    if seconds > 0.8 * CHECK_SECONDS:
        raise ValueError(f'The suite took {seconds:.0f} s on the base commit; acceptance allows {CHECK_SECONDS} s per run. '
                         'Narrow --pytest-args (for example with -m) so the suite takes under about 12 minutes')
    tolerated = sorted(key for key, outcome in outcomes.items() if outcome != 'passed')
    failing = sum(outcome == 'failed' for outcome in outcomes.values())
    acceptance = out / 'acceptance'
    acceptance.mkdir(parents=True)
    shutil.copy2(RECIPE, acceptance / 'check.py')
    (acceptance / 'baseline_failures.json').write_text(json.dumps(tolerated, indent=1) + '\n')
    check = [*prefix, 'python', '/acceptance/check.py', *PYTEST[3:], *arguments]
    targeted = shlex.join([*prefix, *PYTEST, *arguments])
    task = {'repo': str(repo), 'acceptance': 'acceptance', 'profile': 'python-project',
            'objective': objective.strip() + FOOTER.format(targeted=targeted, failing=failing),
            'checks': [check], 'test_command': check, 'max_attempts': max_attempts, 'max_turns': max_turns}
    (out / 'task.json').write_text(json.dumps(task, indent=1) + '\n')
    return {'task': str(out / 'task.json'), 'tests': len(outcomes), 'failing_on_base': failing,
            'skipped_on_base': len(tolerated) - failing, 'base_seconds': round(seconds)}
