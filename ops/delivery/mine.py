"""Mine delivery tasks from a repository's history and validate them in a prepared environment (rig).

A candidate commit changes source and tests together. Its base is the parent commit; its hidden
acceptance is the commit's test files. The task is valid when some hidden tests fail on the base
(with the hidden test files overlaid) and pass on the commit (fail-to-pass, F2P). The full suite
passing on both base and commit is the regression guard (pass-to-pass, P2P).

usage: mine.py SOURCE_GIT SUBDIR OUT --store STORE --commits C1,C2,... [--env K=V ...] [--marker EXPR]
Writes OUT/<commit>/{base,commit}/ and OUT/<commit>/record.json; prints one summary line per commit.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gflo.environment import EnvironmentStore  # noqa: E402
from gflo.prepare import prepare  # noqa: E402
from ops.delivery.env_exec import pytest_outcomes  # noqa: E402


HIDDEN = re.compile(r'^(tests/|test_support/|conftest\.py$)')
MANIFESTS = re.compile(r'^(pyproject\.toml|uv\.lock|requirements[^/]*\.txt|constraints[^/]*\.txt)$')


def git(source, *args):
    return subprocess.run(['git', '-C', str(source), *args], check=True, capture_output=True).stdout


def export(source, commit, subdir, destination):
    data = git(source, 'archive', '--format=tar', f'{commit}:{subdir}' if subdir not in ('', '.') else commit)
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(destination, filter='data')


def changed(source, commit, subdir):
    """(status, path relative to subdir) for every file the commit touched under subdir."""
    lines = git(source, 'diff-tree', '--no-commit-id', '-r', '--name-status', '--no-renames',
                f'{commit}^', commit, '--', subdir or '.').decode().splitlines()
    strip = 0 if subdir in ('', '.') else len(subdir) + 1
    return [(line.split('\t')[0], line.split('\t')[1][strip:]) for line in lines]




def manifest_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.iterdir()):
        if MANIFESTS.match(path.name):
            digest.update(path.name.encode() + b'\0' + path.read_bytes())
    return digest.hexdigest()


def environment_for(store, root, cache):
    key = manifest_hash(root)
    if key not in cache:
        cache[key] = prepare(EnvironmentStore(store), 'python-project', project=root).id
    return cache[key]


def pytest(store, environment, workspace, env, marker, targets, timeout=1500):
    command = ['env', *env, 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-m', marker, *targets]
    return pytest_outcomes(store, environment, workspace, command, timeout)


def mine(source, subdir, out, store, commit, env, marker, cache):
    root = out / commit
    if root.exists():
        shutil.rmtree(root)
    base, after = root / 'base', root / 'commit'
    export(source, commit + '^', subdir, base)
    export(source, commit, subdir, after)
    touched = changed(source, commit, subdir)
    hidden = [(status, path) for status, path in touched if HIDDEN.match(path)]
    source_files = [path for status, path in touched if not HIDDEN.match(path) and path.endswith('.py')]
    record = {'commit': commit, 'subject': git(source, 'log', '-1', '--format=%s', commit).decode().strip(),
              'subdir': subdir, 'hidden': hidden, 'source_files': source_files,
              'manifests_changed': any(MANIFESTS.match(path) for _, path in touched)}
    overlay = root / 'base-hidden'
    shutil.copytree(base, overlay)
    for status, path in hidden:
        target = overlay / path
        if status == 'D':
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(after / path, target)
    environment = environment_for(store, base, cache)
    record['environment'] = environment
    targets = sorted(path for status, path in hidden if status != 'D' and re.search(r'(^|/)test_[^/]*\.py$', path))
    if not targets:
        record['valid'] = False
        record['reason'] = 'no hidden test modules'
        return record
    at_commit, _ = pytest(store, environment, after, env, marker, targets)
    at_base, base_run = pytest(store, environment, overlay, env, marker, targets)
    f2p = sorted(node for node, passed in at_commit.items() if passed and not at_base.get(node))
    record['f2p'] = f2p
    record['hidden_p2p'] = sorted(node for node, passed in at_commit.items() if passed and at_base.get(node))
    record['base_hidden_tail'] = base_run['output'][-1500:]
    suite_base, _ = pytest(store, environment, base, env, marker, ['tests'])
    suite_commit, _ = pytest(store, environment, after, env, marker, ['tests'])
    record['suite_p2p'] = sorted(node for node, passed in suite_base.items()
                                 if passed and suite_commit.get(node))
    record['valid'] = bool(f2p) and not record['manifests_changed']
    record['reason'] = 'ok' if record['valid'] else ('manifests changed' if f2p else 'no fail-to-pass tests')
    shutil.rmtree(overlay)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('subdir')
    parser.add_argument('out', type=Path)
    parser.add_argument('--store', required=True)
    parser.add_argument('--commits', required=True)
    parser.add_argument('--env', action='append', default=[])
    parser.add_argument('--marker', default='not db and not llm and not garmin')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    cache_path = args.out / 'environments.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    for commit in args.commits.split(','):
        try:
            record = mine(args.source, args.subdir, args.out, args.store, commit, args.env, args.marker, cache)
        except Exception as error:  # one bad candidate must not stop the batch
            record = {'commit': commit, 'valid': False, 'reason': f'{type(error).__name__}: {error}'[:500]}
            (args.out / commit).mkdir(parents=True, exist_ok=True)
        record['test_command'] = ['env', *args.env, 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-m', args.marker, 'tests']
        (args.out / commit / 'record.json').write_text(json.dumps(record, indent=1) + '\n')
        cache_path.write_text(json.dumps(cache, indent=1) + '\n')
        print(commit, record['valid'], record['reason'], len(record.get('f2p', [])), len(record.get('suite_p2p', [])), flush=True)
