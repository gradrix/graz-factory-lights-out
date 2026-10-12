"""Change queue (roadmap phase 4): run a feature as ordered change tasks on an integration branch (usage: README).

The controller clones the repository into OUT/integration (with no remote, so nothing can be pushed back), builds
each step's task from the integration branch's current head with `gflo task init` acceptance, runs it as an ordinary
`gflo run` subprocess, and commits the accepted patch onto the branch. Each step starts from the previous accepted
state, so its acceptance (no new suite failures, review) ran on exactly the tree that gets committed. A step that
ends without acceptance stops the queue; a run that could not start or was interrupted is retried by the next
invocation. The source repository is only read.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from .overnight import FINAL, outcome

BRANCH = 'gflo/queue'
MANIFEST = re.compile(r'pyproject\.toml|uv\.lock|(requirements|constraints)[^/]*\.txt')  # prepare.manifest_names


def git(repo, *args, **kwargs):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True, **kwargs).stdout.strip()


def load(spec):
    spec = json.loads(Path(spec).read_text())
    steps = spec.get('steps') or []
    if not steps or not all(isinstance(step, dict) and str(step.get('objective', '')).strip() for step in steps):
        raise ValueError('The queue needs "steps": a list of {"id", "objective"} in dependency order')
    ids = [str(step.get('id') or index + 1) for index, step in enumerate(steps)]
    if len(set(ids)) != len(ids) or not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name) for name in ids):
        raise ValueError('Step ids must be unique and use only letters, digits, ".", "_" and "-"')
    return spec, [dict(step, id=name) for name, step in zip(ids, steps)]


def fingerprint(steps):
    return hashlib.sha256(json.dumps([[step['id'], step['objective']] for step in steps]).encode()).hexdigest()


def integration(repo, out, base):
    """OUT/integration: a clone of REPO with BRANCH at BASE (created once) and no remote."""
    clone = out / 'integration'
    if not (clone / '.git').exists():
        shutil.rmtree(clone, ignore_errors=True)
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', str(repo), str(clone)], check=True, capture_output=True)
        git(clone, 'checkout', '-q', '-B', BRANCH, base)
        git(clone, 'remote', 'remove', 'origin')
    return clone


def merge(clone, step, result):
    """Commit RESULT's accepted patch for STEP on the branch; returns the commit, or a final refusal in RESULT."""
    marker = f'(run {result["run"]})'
    if marker in git(clone, 'log', '-1', '--format=%s'):
        return git(clone, 'rev-parse', 'HEAD')  # committed before an interruption, not yet recorded
    git(clone, 'reset', '-q', '--hard')  # discard a half-applied patch from an interruption
    patch = Path(result['patch'])
    if patch.read_bytes().strip():
        applied = subprocess.run(['git', '-C', str(clone), 'apply', '--index', '--binary', str(patch)], capture_output=True, text=True)
        if applied.returncode:
            result.update(status='not integrated', detail=('git apply failed: ' + applied.stderr.strip())[:300])
            return None
    manifests = [name for name in git(clone, 'diff', '--cached', '--name-only').splitlines() if MANIFEST.fullmatch(name)]
    if manifests:
        git(clone, 'reset', '-q', '--hard')
        result.update(status='not integrated', detail=f'changes dependency manifests ({", ".join(manifests)}); a queue runs in one '
                      'prepared environment, so make this change by hand and start a new queue from it')
        return None
    git(clone, '-c', 'user.name=gflo', '-c', 'user.email=gflo@local', 'commit', '-q', '--allow-empty',
        '-m', f'gflo queue step {step["id"]} {marker}', '-m', step['objective'].strip())
    return git(clone, 'rev-parse', 'HEAD')


def run_queue(spec_path, out, *, state, config, environment_store, environment=None, build_task=None, command=None,
              status=None):
    """Run the queue in SPEC_PATH; returns {"report": OUT/report.md, "committed": steps on the branch, "steps": total}."""
    spec, steps = load(spec_path)
    repo = (Path(spec_path).parent / spec['repo']).resolve()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    queue_path = out / 'queue.json'
    if queue_path.exists():
        queue = json.loads(queue_path.read_text())
        if queue['repo'] != str(repo):
            raise ValueError(f'{queue_path} belongs to another repository: {queue["repo"]}')
    else:
        if git(repo, 'status', '--porcelain'):
            raise ValueError('Repository must be clean; commit the intended base first')
        queue = {'repo': str(repo), 'base': git(repo, 'rev-parse', 'HEAD'), 'steps': fingerprint(steps), 'done': {}}
    if queue.get('steps') != fingerprint(steps):
        raise ValueError(f'The steps in {spec_path} changed since this queue started; use a new --out directory')
    clone = integration(repo, out, queue['base'])
    pending = [done for done in queue['done'].values() if done.get('status') == 'accepted' and not done.get('commit')]
    if git(clone, 'status', '--porcelain', '--untracked-files=no') and not pending:
        raise ValueError(f'{clone} has uncommitted changes; the controller owns this clone')
    command = command or [sys.executable, '-m', 'gflo']
    report = out / 'report.md'
    try:
        for step in steps:
            done = queue['done'].get(step['id'], {})
            if done.get('status') == 'accepted' and not done.get('commit'):  # interrupted while integrating
                done['commit'] = merge(clone, step, done)
                queue_path.write_text(json.dumps(queue, indent=1) + '\n')
            if done.get('commit'):
                continue
            if done.get('status') in FINAL | {'not integrated'}:
                break  # ended without acceptance: later steps depend on it
            directory = out / 'steps' / step['id']
            if not (directory / 'task.json').exists():
                shutil.rmtree(directory, ignore_errors=True)
                directory.parent.mkdir(parents=True, exist_ok=True)
                try:
                    build_task(clone, step['objective'], directory)
                except (ValueError, OSError, subprocess.SubprocessError) as error:
                    queue['done'][step['id']] = {'status': 'not built', 'detail': str(error)[:300]}
                    break
            run = [*command, '--state', str(state), '--config', str(config), 'run', str(directory / 'task.json'),
                   '--environment-store', str(environment_store)] + (['--environment', environment] if environment else [])
            completed = subprocess.run(run, capture_output=True, text=True)
            log = completed.stdout + completed.stderr
            (directory / 'run.log').write_text(log)
            result = outcome(state, log, status)
            queue['done'][step['id']] = result
            queue_path.write_text(json.dumps(queue, indent=1) + '\n')  # an accepted run is recorded before integration
            if result['status'] == 'accepted':
                result['commit'] = merge(clone, step, result)
                queue_path.write_text(json.dumps(queue, indent=1) + '\n')
            if not result.get('commit'):
                break
        head = git(clone, 'rev-parse', 'HEAD')
        (out / 'feature.patch').write_text(git(clone, 'diff', '--binary', queue['base'], head) + '\n' if head != queue['base'] else '')
    finally:
        queue_path.write_text(json.dumps(queue, indent=1) + '\n')
        report.write_text(queue_report(queue, steps, clone))
    committed = sum(bool(queue['done'].get(step['id'], {}).get('commit')) for step in steps)
    return {'report': str(report), 'committed': committed, 'steps': len(steps)}


def queue_report(queue, steps, clone):
    merged = [step['id'] for step in steps if queue['done'].get(step['id'], {}).get('commit')]
    complete = len(merged) == len(steps)
    lines = [f'# Change queue: {queue["repo"]}', '',
             f'{len(merged)} of {len(steps)} steps accepted and committed on branch `{BRANCH}` of `{clone}`'
             + (' — the feature is complete.' if complete else '.'),
             f'Base commit `{queue["base"][:12]}`. The source repository was not changed. '
             + ('Review `feature.patch` (base to branch head) before applying it.' if merged else ''), '',
             '| Step | Result | Run | Commit |', '|---|---|---|---|']
    for step in steps:
        value = queue['done'].get(step['id'])
        if value is None:
            cells = [step['id'], 'not reached', '—', '—']
        else:
            result = value['status'] + (f', {value["attempts"]} attempts' if value.get('attempts', 1) > 1 else '')
            if value['status'] not in FINAL and value.get('detail'):
                result += f': {value["detail"]}'
            cells = [step['id'], result, value.get('run', '—'), f'`{value["commit"][:12]}`' if value.get('commit') else '—']
        lines.append('| ' + ' | '.join(str(cell).replace('|', '\\|').replace('\n', ' ') for cell in cells) + ' |')
    stopped = [step['id'] for step in steps if queue['done'].get(step['id'], {}).get('status') in (FINAL - {'accepted'}) | {'not integrated'}]
    if stopped:
        lines += ['', f'Step {stopped[0]} ended without acceptance or integration, so the later steps did not run. '
                  'Revise its objective, then remove its entry from queue.json and its directory under steps/ to retry it.']
    return '\n'.join(lines) + '\n'
