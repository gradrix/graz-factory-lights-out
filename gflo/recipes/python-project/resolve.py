"""Resolve a project's own declared dependencies plus pytest into a disposable tree.

Runs in the preparation container: manifests at /inputs, network enabled for the whole
resolution (sdist builds included). `check` parses the manifests offline; `resolve` installs and writes
a tar of the tree (with the resolved lock as gflo-lock.json) to stdout.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tomllib

TEST_RUNNER = 'pytest'  # unpinned: the project's constraints or plugins choose the version
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9._,\s-]+\])?')
DENIED = re.compile(r'(://|@|^\s*-|\s-|^\s*\.|^\s*/|\\)')


def normalized(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def requirement(line, source):
    if not isinstance(line, str):
        raise ValueError(f'{source}: dependency entries must be strings')
    line = line.split('#', 1)[0].strip()
    if not line:
        return None
    if DENIED.search(line) or not NAME.match(line):
        raise ValueError(f'{source}: only named PyPI requirements are supported (no URLs, paths, options or includes): {line}')
    return line


def requirements(root):
    """Declared runtime and optional dependencies; the project itself is never built."""
    root = Path(root)
    found = []
    pyproject = root / 'pyproject.toml'
    texts = sorted(root.glob('requirements*.txt'))
    if pyproject.is_file():
        value = tomllib.loads(pyproject.read_text())
        project = value.get('project')
        if project is None and not texts:
            raise ValueError('pyproject.toml has no [project] table (Poetry and dependency-groups are unsupported); add requirements*.txt')
        project = project or {}
        if 'dependencies' in project.get('dynamic', []):
            raise ValueError('pyproject.toml: dynamic dependencies are not supported')
        own = normalized(str(project.get('name', '')))
        groups = [project.get('dependencies', [])] + list(project.get('optional-dependencies', {}).values())
        for group in groups:
            for item in group:
                if isinstance(item, str) and own and normalized(re.split(r'[\[<>=!~;\s]', item, maxsplit=1)[0]) == own:
                    continue  # self-referencing extra such as "pkg[dev]"
                found.append(requirement(item, 'pyproject.toml'))
    elif not texts:
        raise ValueError('python-project needs pyproject.toml or requirements*.txt')
    for path in texts:
        for line in path.read_text().splitlines():
            found.append(requirement(line, path.name))
    return sorted({item for item in found if item})


def constraints(root):
    """Root constraints*.txt files pin versions the way the project's own builds do (pip -c)."""
    found = []
    for path in sorted(Path(root).glob('constraints*.txt')):
        for line in path.read_text().splitlines():
            found.append(requirement(line, path.name))
    return sorted({item for item in found if item})


def requested(root):
    """Declared requirements plus pytest unless a requirement names it; constraints only choose versions."""
    found = requirements(root)
    names = {normalized(re.split(r"[\[<>=!~;\s]", item, maxsplit=1)[0]) for item in found}
    return found if "pytest" in names else found + [TEST_RUNNER]


def resolve(root):
    work = Path('/work')
    deps, tmp = work / 'deps', work / 'tmp'
    tmp.mkdir()
    os.environ['TMPDIR'] = str(tmp)
    listed = work / 'requirements.txt'
    listed.write_text('\n'.join(requested(root)) + '\n')
    pinned = work / 'constraints.txt'
    pinned.write_text(''.join(item + '\n' for item in constraints(root)))
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--isolated', '--no-cache-dir', '--no-compile',
                    '--disable-pip-version-check', '--progress-bar', 'off', '--prefer-binary',
                    '--index-url', 'https://pypi.org/simple', '--target', str(deps),
                    '--report', str(work / 'report.json'), '-c', str(pinned), '-r', str(listed)],
                   check=True, stdout=sys.stderr, env={k: v for k, v in os.environ.items() if k != 'PIP_NO_INDEX'})
    report = json.loads((work / 'report.json').read_text())
    lock = sorted(({'name': item['metadata']['name'], 'version': item['metadata']['version'],
                    'url': item['download_info']['url'],
                    'hashes': item['download_info'].get('archive_info', {}).get('hashes', {})}
                   for item in report['install']), key=lambda item: item['name'].lower())
    (deps / 'gflo-lock.json').write_text(json.dumps({'requested': requested(root), 'constraints': constraints(root), 'resolved': lock},
                                                    indent=1, sort_keys=True) + '\n')
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        for path in sorted(deps.rglob('*')):
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                continue  # pip --target never needs links; skip rather than publish them
            header = archive.gettarinfo(str(path), arcname=path.relative_to(deps).as_posix())
            header.uid = header.gid = header.mtime = 0
            header.uname = header.gname = ''
            header.mode = 0o555 if path.is_dir() or path.stat().st_mode & 0o111 else 0o444
            if path.is_file():
                with path.open('rb') as source:
                    archive.addfile(header, source)
            else:
                archive.addfile(header)


if __name__ == '__main__':
    if sys.argv[1:] == ['check']:
        print(json.dumps({'passed': True, 'requirements': requested('/inputs'), 'constraints': constraints('/inputs')}))
    elif sys.argv[1:] == ['resolve']:
        resolve('/inputs')
    else:
        raise SystemExit('usage: resolve.py check|resolve')
