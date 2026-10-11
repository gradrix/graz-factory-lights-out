"""Overnight test queue (roadmap phase 3): walk a repository's modules, one test-writing run each, then a morning report.

Each module gets its own `gflo tests init` task and an ordinary `gflo run` in a subprocess, one at a time (the model
has one slot), so a failing run never stops the queue. queue.json records each finished module; a rerun of the same
command skips them. No new run starts after the time budget ends. report.md lists what was accepted, how strong the
new tests are and where each patch is; nothing is applied to the repository.
"""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from .testfactory import RECIPE, build, tracked

MIN_SITES = 5
SKIP = {'setup.py', 'conftest.py', '__main__.py', '__init__.py'}


def recipe():
    import importlib.util
    spec = importlib.util.spec_from_file_location('test_acceptance', RECIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def importers(tests_sources, name):
    """How many test modules import module NAME directly (a package import does not count)."""
    count = 0
    for source in tests_sources:
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError, RecursionError):
            continue
        if any((isinstance(node, ast.Import) and any(alias.name == name for alias in node.names))
               or (isinstance(node, ast.ImportFrom) and node.module and (
                   node.module == name or any(f'{node.module}.{alias.name}' == name for alias in node.names)))
               for node in ast.walk(tree)):
            count += 1
    return count


def candidates(repo, limit=None):
    """Tracked non-test modules with at least MIN_SITES mutation sites: least directly tested first, then largest."""
    tests = recipe()
    repo = Path(repo)
    files = tracked(repo)
    sources = [(repo / name).read_text(errors='replace') for name in files if tests.is_test(name) and name.endswith('.py')]
    ranked = []
    for name in files:
        if not name.endswith('.py') or tests.is_test(name) or Path(name).name in SKIP or (repo / name).is_symlink():
            continue
        try:
            sites = len(tests.mutation_sites(ast.parse((repo / name).read_text(errors='replace'))))
        except (SyntaxError, ValueError, RecursionError):
            continue
        if sites >= MIN_SITES:
            ranked.append((importers(sources, tests.module_name(name)), -sites, name))
    ranked.sort()
    return [{'target': name, 'tested_by': tested, 'sites': -sites} for tested, sites, name in ranked][:limit]


def slug(target):
    return re.sub(r'[^A-Za-z0-9]+', '-', target.removesuffix('.py')).strip('-')


def outcome(state, log, status=None):
    """Factory status, attempts and the acceptance summary of the last attempt, from the run's evidence."""
    found = re.search(r'^Run: ([0-9a-f]{12})$', log, re.M)
    if not found:
        return {'status': 'not started', 'detail': log.strip().splitlines()[-1][:300] if log.strip() else ''}
    if status is None:
        from .runner import Factory
        status = Factory(state, None, None).status
    run = Path(state) / found.group(1)
    result = {'run': found.group(1), 'status': status(found.group(1)).get('status', 'unknown'),
              'patch': str(run / 'change.patch')}
    attempts = sorted((run / 'attempts').glob('*/verification.json'), key=lambda path: int(path.parent.name))
    result['attempts'] = len(attempts)
    if attempts:
        checks = json.loads(attempts[-1].read_text()).get('checks') or [{}]
        result['acceptance'] = (checks[0].get('output') or '').strip()[:1500]
    return result


def night(repo, out, *, state, config, environment_store, environment=None, limit=None, hours=8.0,
          threshold=0.6, checks_env=(), profile='python-project', command=None, clock=time.monotonic, status=None):
    """Run the queue; returns the path of the morning report."""
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    queue_path = out / 'queue.json'
    queue = json.loads(queue_path.read_text()) if queue_path.exists() else {'repo': str(Path(repo).resolve()), 'done': {}}
    if queue['repo'] != str(Path(repo).resolve()):
        raise ValueError(f'{queue_path} belongs to another repository: {queue["repo"]}')
    planned = candidates(repo, limit)
    queue['planned'] = planned
    command = command or [sys.executable, '-m', 'gflo']
    deadline = clock() + hours * 3600
    for item in planned:
        target = item['target']
        if target in queue['done']:
            continue
        if clock() >= deadline:
            break
        directory = out / slug(target)
        started = clock()
        if not (directory / 'task.json').exists():
            try:
                build(repo, [target], directory, threshold=threshold, profile=profile, checks_env=checks_env)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                queue['done'][target] = {'status': 'not built', 'detail': str(error)[:300]}
                queue_path.write_text(json.dumps(queue, indent=1) + '\n')
                continue
        run = [*command, '--state', str(state), '--config', str(config), 'run', str(directory / 'task.json'),
               '--environment-store', str(environment_store)] + (['--environment', environment] if environment else [])
        completed = subprocess.run(run, capture_output=True, text=True)
        log = completed.stdout + completed.stderr
        (directory / 'run.log').write_text(log)
        queue['done'][target] = dict(outcome(state, log, status), seconds=round(clock() - started))
        queue_path.write_text(json.dumps(queue, indent=1) + '\n')
    report = out / 'report.md'
    report.write_text(morning_report(queue))
    return report


def morning_report(queue):
    done, planned = queue['done'], queue.get('planned', [])
    accepted = [target for target, value in done.items() if value['status'] == 'accepted']
    lines = [f'# Overnight tests: {queue["repo"]}', '',
             f'{len(accepted)} of {len(done)} modules accepted; {len(planned) - len(done)} of {len(planned)} planned not reached.',
             'Nothing was applied to the repository. Review each accepted patch before merging it.', '',
             '| Module | Tested by (before) | Result | Time | New tests | Patch |', '|---|---|---|---|---|---|']
    tested = {item['target']: item['tested_by'] for item in planned}
    for target, value in done.items():
        summary = (value.get('acceptance') or value.get('detail') or '').splitlines()
        first = summary[0] if summary else ''
        strength = re.search(r'(\d+) new test functions.*?kill (\d+/\d+ = [\d.]+)', first)
        tests = f'{strength.group(1)} tests, kill {strength.group(2)}' if strength else first[:120].replace('|', '/')
        result = value['status'] + (f', {value["attempts"]} attempts' if value.get('attempts', 1) > 1 else '')
        patch = f'`{value["patch"]}`' if value['status'] == 'accepted' else '—'
        lines.append(f'| `{target}` | {tested.get(target, "?")} | {result} | {value.get("seconds", 0)} s | {tests} | {patch} |')
    survivors = [(target, line) for target in accepted for line in (done[target].get('acceptance') or '').splitlines()
                 if line.startswith('SURVIVED')]
    if survivors:
        lines += ['', 'Mutants the accepted tests still miss (possible gaps or equivalent mutants):', '']
        lines += [f'- `{target}`: {line.removeprefix("SURVIVED ")}' for target, line in survivors]
    return '\n'.join(lines) + '\n'
