"""Model-gate benchmark seed: pack the parts git cannot regenerate, or rebuild the benchmark from them (rig).

  bench.py pack BENCH SEED      # writes SEED/manifest.json and SEED/<source>.json (one per source repository)
  bench.py build SEED BENCH --source home-lab=GIT --source gflo=GIT

The seed holds the manifest, each task's definition (objective, checks), its mined record (hidden fail-to-pass
and pass-to-pass test lists), the tests already failing on its base, and the feature step objectives: a few MB
of text. `build` exports every code tree from the source repositories at the recorded commits, creates the
task repositories as ops/delivery/tasks.py does, and prepares the environments again. The committed copy is
ops/benchmark/seed/ (home-lab.json encrypted, because it describes private code); docs/model-upgrade.md.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SUITES = ('small', 'features')


def groups(manifest):
    return [group for suite in SUITES for group in manifest[suite]]


def seed_files(group):
    """Relative paths of one group's seed files, per commit."""
    for commit in group['commits']:
        yield f"{group['mined']}/{commit}/record.json"
        yield f"{group['mined']}/{commit}/baseline_failures.json"
        yield f"{group['tasks']}/{commit}/task.json"
        yield f"{group['tasks']}/{commit}/acceptance/baseline_failures.json"
        yield f"{group['tasks']}/{commit}/acceptance/check.py"
    if group.get('steps'):
        yield group['steps']


def pack(bench, seed):
    bench, seed = Path(bench), Path(seed)
    manifest = json.loads((bench / 'manifest.json').read_text())
    seed.mkdir(parents=True, exist_ok=True)
    by_source = {}
    for group in groups(manifest):
        files = by_source.setdefault(group['source'], {})
        for path in seed_files(group):
            files[path] = (bench / path).read_text()
    for source, files in by_source.items():
        (seed / f'{source}.json').write_text(json.dumps(files, indent=0, sort_keys=True) + '\n')
    (seed / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    return {source: len(files) for source, files in by_source.items()}


def git_init(repo, message):
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=gflo', '-c', 'user.email=gflo@local',
                    'commit', '-qm', message], check=True)


def build(seed, bench, sources):
    from ops.delivery.mine import environment_for, export
    from ops.delivery.tasks import task_environment
    seed, bench = Path(seed), Path(bench)
    if bench.exists():
        raise SystemExit(f'{bench} exists; build into a new directory')
    manifest = json.loads((seed / 'manifest.json').read_text())
    store = bench / 'envs'
    store.mkdir(parents=True)
    store.chmod(0o700)  # gflo.environment refuses a store others can write
    for source in {group['source'] for group in groups(manifest)}:
        for path, text in json.loads((seed / f'{source}.json').read_text()).items():
            (bench / path).parent.mkdir(parents=True, exist_ok=True)
            (bench / path).write_text(text)
    for group in groups(manifest):
        git = sources[group['source']]
        cache_path = bench / group['mined'] / 'environments.json'
        cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        for commit in group['commits']:
            mined, task = bench / group['mined'] / commit, bench / group['tasks'] / commit
            record = json.loads((mined / 'record.json').read_text())
            export(git, record.get('base') or commit + '^', record['subdir'], mined / 'base')
            export(git, commit, record['subdir'], mined / 'commit')
            record['environment'] = environment_for(str(store), mined / 'base', cache)
            (mined / 'record.json').write_text(json.dumps(record, indent=1) + '\n')
            shutil.copytree(mined / 'base', task / 'repo')
            git_init(task / 'repo', f'base of {commit}')
            environment = task_environment(str(store), task / 'repo', bench / group['tasks'] / 'environments.json')
            (task / 'environment.txt').write_text(environment + '\n')
            print(group['tasks'], commit, environment[:12], flush=True)
        cache_path.write_text(json.dumps(cache, indent=1) + '\n')
    tests = manifest['tests']
    export(sources[tests['source']], tests['commit'], tests['subdir'], bench / tests['repo'])
    git_init(bench / tests['repo'], 'base')
    shutil.copy2(seed / 'manifest.json', bench / 'manifest.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    pack_parser = sub.add_parser('pack')
    pack_parser.add_argument('bench')
    pack_parser.add_argument('seed')
    build_parser = sub.add_parser('build')
    build_parser.add_argument('seed')
    build_parser.add_argument('bench')
    build_parser.add_argument('--source', action='append', default=[], help='NAME=GIT (repository path or bundle)')
    args = parser.parse_args()
    if args.action == 'pack':
        print(pack(args.bench, args.seed))
    else:
        build(args.seed, args.bench, dict(pair.split('=', 1) for pair in args.source))
