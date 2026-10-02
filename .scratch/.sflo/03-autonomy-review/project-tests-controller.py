"""Coordinator regression probe using the published frozen failing candidate."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from gflo.runner import Factory
from gflo.sandbox import Sandbox

repo = Path(__file__).resolve().parents[3]
fixture = repo / 'evaluations/coding-b/tasks/02-rate-window'
evidence = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='gflo-project-tests-') as directory:
    root = Path(directory)
    source = root / 'source'
    shutil.copytree(fixture / 'source', source)
    subprocess.run(['git', 'init', '-q', str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'apply', str(evidence / 'coding-b-evidence/02-rate-window/source.patch')], check=True)
    subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(source), '-c', 'user.name=Probe', '-c', 'user.email=probe@local', 'commit', '-qm', 'Frozen failing regression candidate'], check=True)
    task = json.loads((fixture / 'task.json').read_text())
    task.update(repo=str(source), acceptance=str(fixture / 'acceptance'), max_attempts=2)
    task_path = root / 'task.json'
    task_path.write_text(json.dumps(task))
    review_calls = []
    def worker(workspace, task, previous, attempt):
        if attempt == 2:
            assert previous['passed'] is False
            assert previous['checks'][0]['exit_code'] == 0
            assert previous['checks'][-1]['exit_code'] != 0
            path = workspace / 'tests/test_admit.py'
            text = path.read_text()
            start = text.index('    def test_retry_when_count_exceeds_limit')
            end = text.index('    def ', start + 5)
            text = text[:start] + text[start:end].replace('"retry_at": 20', '"retry_at": 21') + text[end:]
            path.write_text(text)
            with (workspace / 'README.md').open('a') as f:
                f.write('\nUse action admit with history, now, window and limit to return allowed, history and retry_at.\n')
        return {}
    def review(*args):
        review_calls.append(True)
        return dict(decision='pass', findings=[], question='')
    factory = Factory(root / 'state', worker, Sandbox().verify, reviewer=review)
    run = factory.create(task_path)
    result = factory.resume(run)
    assert result['status'] == 'accepted' and result['attempts'] == 2
    assert len(review_calls) == 1
    attempts = [json.loads(p.read_text()) for p in sorted((root / 'state' / run / 'attempts').glob('*/verification.json'))]
    receipt = {'candidate': 'c17821c', 'verification': 'coordinator; no local model or fresh QA agent', 'source': 'frozen cohort-B task02 patch', 'accepted_attempt': 2, 'review_calls': len(review_calls), 'attempts': attempts}
    (evidence / 'project-tests-controller.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('FAIL generated test -> repair -> all checks PASS -> review -> accepted attempt 2')
