"""Offline installation of a fixed wheel set into a disposable dependency tree."""
from pathlib import Path
import os
import subprocess
import sys
import tarfile

root = Path('/work/deps')
Path('/work/tmp').mkdir()
os.environ['TMPDIR'] = '/work/tmp'
subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-cache-dir',
                '--no-compile', '--no-deps', '--require-hashes', '--only-binary=:all:',
                '--find-links', '/artifacts', '--target', str(root),
                '-r', '/approved/requirements.lock'], check=True, stdout=sys.stderr)
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError('Unsupported dependency file type')
        header = archive.gettarinfo(str(path), arcname=path.relative_to(root).as_posix())
        header.uid = header.gid = header.mtime = 0
        header.uname = header.gname = ''
        header.mode = 0o555 if path.is_dir() or path.stat().st_mode & 0o111 else 0o444
        if path.is_file():
            with path.open('rb') as source:
                archive.addfile(header, source)
        else:
            archive.addfile(header)
