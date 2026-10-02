"""Reconstruct reviewed Git source temporarily; never import a moving checkout."""
import atexit
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

INITIAL = 'ba364023ad90bcea68193ff1c5ddf8e6971f7b07'
RECHECK = '197371ea5dc47b4aad77f3ac1f2a79c2a72f2410'


def activate(commit):
    repo = subprocess.check_output(
        ['git', '-C', str(Path(__file__).resolve().parent), 'rev-parse', '--show-toplevel'], text=True).strip()
    archive = subprocess.check_output(['git', '-C', repo, 'archive', commit])
    temporary = tempfile.TemporaryDirectory(prefix='gflo-qa-' + commit[:7] + '-')
    atexit.register(temporary.cleanup)
    root = Path(temporary.name)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(root, filter='data')
    sys.path.insert(0, str(root))
    os.environ['PYTHONPATH'] = str(root)
    return root


def evidence(default):
    return Path(os.environ.get('GFLO_QA_EVIDENCE', str(Path(__file__).resolve().parent / default))).resolve()


if __name__ == '__main__':
    root = activate(sys.argv[1])
    raise SystemExit(subprocess.call([sys.executable, *sys.argv[2:]], cwd=root))
