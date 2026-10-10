"""Turn validated mined records into factory tasks, and score finished runs against hidden tests (rig).

  tasks.py build MINED OBJECTIVES TASKS     # one task dir per valid record that has an objective
  tasks.py score MINED TASKS RUN_STATE STORE COMMIT RUN_ID   # prints and saves the score JSON

The worker only sees the base commit and the objective. Scoring overlays the commit's test files
on the run's final workspace and requires every fail-to-pass test and every suite pass-to-pass
test to pass. "delivered" additionally requires the factory to have accepted the run.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.delivery.env_exec import pytest_outcomes  # noqa: E402



def build(mined, objectives, tasks):
    objectives = json.loads(Path(objectives).read_text())
    built = []
    for record_path in sorted(Path(mined).glob('*/record.json')):
        record = json.loads(record_path.read_text())
        commit = record['commit']
        if not record.get('valid') or commit not in objectives:
            continue
        root = Path(tasks) / commit
        if root.exists():
            shutil.rmtree(root)
        repo = root / 'repo'
        shutil.copytree(record_path.parent / 'base', repo)
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=gflo', '-c', 'user.email=gflo@local',
                        'commit', '-qm', f'base of {commit}'], check=True)
        acceptance = root / 'acceptance'
        acceptance.mkdir()
        (acceptance / 'README.md').write_text('Acceptance is the project suite (checks); hidden tests are scored separately.\n')
        task = {'repo': 'repo', 'acceptance': 'acceptance', 'profile': 'python-project',
                'objective': objectives[commit], 'checks': [record['test_command']],
                'test_command': record['test_command'], 'max_attempts': 3, 'max_turns': 40}
        (root / 'task.json').write_text(json.dumps(task, indent=1) + '\n')
        built.append(commit)
    return built


def score(mined, tasks, state, store, commit, run_id):
    record = json.loads((Path(mined) / commit / 'record.json').read_text())
    run = Path(state) / run_id
    from gflo.runner import Factory
    status = Factory(state, None, None).status(run_id)
    work = Path(tasks) / commit / 'score' / run_id
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(run / 'workspace', work)
    after = Path(mined) / commit / 'commit'
    for change, path in record['hidden']:
        target = work / path
        if change == 'D':
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(after / path, target)
    seen, result = pytest_outcomes(store, record['environment'], work, record['test_command'], timeout=1500)
    f2p_failed = [node for node in record['f2p'] if not seen.get(node)]
    p2p_failed = [node for node in record['suite_p2p'] + record['hidden_p2p'] if not seen.get(node)]
    value = {'commit': commit, 'run': run_id, 'factory_status': status.get('status'), 'attempts': status.get('attempts'),
             'f2p_total': len(record['f2p']), 'f2p_failed': f2p_failed,
             'p2p_total': len(set(record['suite_p2p'] + record['hidden_p2p'])), 'p2p_failed': sorted(set(p2p_failed)),
             'hidden_pass': not f2p_failed and not p2p_failed, 'tail': result['output'][-1200:]}
    value['delivered'] = value['hidden_pass'] and value['factory_status'] == 'accepted'
    value['false_accept'] = value['factory_status'] == 'accepted' and not value['hidden_pass']
    (work.parent / f'{run_id}.json').write_text(json.dumps(value, indent=1) + '\n')
    shutil.rmtree(work)
    return value


if __name__ == '__main__':
    if sys.argv[1] == 'build':
        print(json.dumps(build(*sys.argv[2:5])))
    elif sys.argv[1] == 'score':
        value = score(*sys.argv[2:8])
        print(json.dumps({k: v for k, v in value.items() if k != 'tail'}))
    else:
        raise SystemExit(__doc__)
