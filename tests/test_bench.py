import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ops.benchmark import bench


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class BenchSeedTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        source = self.root / 'source'
        (source / 'svc').mkdir(parents=True)
        git(source.parent, 'init', '-q', '-b', 'main', str(source))
        for text in ('one', 'two'):
            (source / 'svc' / 'app.py').write_text(text + '\n')
            git(source, 'add', '-A')
            git(source, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', text)
        self.source, self.commit = source, git(source, 'rev-parse', '--short', 'HEAD')
        self.manifest = {'small': [{'tasks': 'small/tasks', 'mined': 'small/mined', 'commits': [self.commit], 'source': 'src'}],
                         'features': [],
                         'tests': {'repo': 'tests/repo', 'source': 'src', 'commit': 'HEAD', 'subdir': 'svc'}}
        old = self.root / 'old'
        files = {'small/mined/C/record.json': json.dumps({'commit': self.commit, 'subdir': 'svc', 'environment': 'old', 'f2p': ['t']}),
                 'small/mined/C/baseline_failures.json': '[]', 'small/tasks/C/task.json': '{"objective": "do it"}',
                 'small/tasks/C/acceptance/baseline_failures.json': '[]', 'small/tasks/C/acceptance/check.py': 'pass\n'}
        for path, text in files.items():
            (old / path.replace('/C/', f'/{self.commit}/')).parent.mkdir(parents=True, exist_ok=True)
            (old / path.replace('/C/', f'/{self.commit}/')).write_text(text)
        (old / 'manifest.json').write_text(json.dumps(self.manifest))
        self.old = old

    def test_pack_keeps_only_seed_files_and_build_restores_the_benchmark_from_git(self):
        (self.old / 'small/tasks' / self.commit / 'repo').mkdir()
        (self.old / 'small/tasks' / self.commit / 'repo' / 'big.bin').write_text('x' * 1000)
        seed = self.root / 'seed'
        self.assertEqual(bench.pack(self.old, seed), {'src': 5})
        self.assertNotIn('big.bin', (seed / 'src.json').read_text())
        new = self.root / 'new'
        with patch('ops.delivery.mine.environment_for', return_value='env-a'), \
                patch('ops.delivery.tasks.task_environment', return_value='env-b'):
            bench.build(seed, new, {'src': str(self.source)})
        mined, task = new / 'small/mined' / self.commit, new / 'small/tasks' / self.commit
        self.assertEqual((mined / 'base' / 'app.py').read_text(), 'one\n')
        self.assertEqual((mined / 'commit' / 'app.py').read_text(), 'two\n')
        record = json.loads((mined / 'record.json').read_text())
        self.assertEqual((record['environment'], record['f2p']), ('env-a', ['t']))
        self.assertEqual((task / 'environment.txt').read_text(), 'env-b\n')
        self.assertEqual((task / 'repo' / 'app.py').read_text(), 'one\n')
        self.assertEqual(git(task / 'repo', 'log', '--format=%s'), f'base of {self.commit}')
        self.assertEqual((task / 'task.json').read_text(), '{"objective": "do it"}')
        self.assertEqual((new / 'tests/repo/app.py').read_text(), 'two\n')
        self.assertEqual(json.loads((new / 'manifest.json').read_text()), self.manifest)
        with self.assertRaises(SystemExit):
            bench.build(seed, new, {'src': str(self.source)})


if __name__ == '__main__':
    unittest.main()
