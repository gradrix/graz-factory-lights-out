"""Controller-owned immutable environment snapshots and their checked receipts."""
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from .artifacts import ArchiveLimits, unpack_archive


HEX = re.compile(r'[0-9a-f]{64}')
PROFILES = ('python-stdlib', 'python-api', 'node-ts', 'python-project')
# Project-resolved dependency trees (pandas, SQLAlchemy, ...) exceed the fixed profiles' bounds.
PROJECT_LIMITS = ArchiveLimits(transport_bytes=3 * 1024 ** 3, entries=200000, expanded_bytes=3 * 1024 ** 3, path_bytes=240)


def limits_for(profile):
    return PROJECT_LIMITS if profile == 'python-project' else ArchiveLimits()


def encoded(value):
    data = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    if len(data) > 65536:
        raise ValueError('Environment receipt exceeds 64 KiB')
    return data


def metadata_checked(value):
    required = {'profile', 'image', 'platform', 'recipe_sha256', 'locks', 'runtime'}
    if not isinstance(value, dict) or not required.issubset(value) or set(value) - required - {'artifacts', 'inputs'}:
        raise ValueError('Incomplete or unsupported environment metadata')
    if value['profile'] not in PROFILES or value['platform'] != 'linux/amd64':
        raise ValueError('Unsupported environment profile or platform')
    if not isinstance(value['image'], str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value['image']):
        raise ValueError('Environment requires an inspected immutable image ID')
    if not isinstance(value['recipe_sha256'], str) or not HEX.fullmatch(value['recipe_sha256']):
        raise ValueError('Environment recipe hash is invalid')
    if not isinstance(value['runtime'], dict) or not value['runtime'] or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in value['runtime'].items()):
        raise ValueError('Environment requires actual runtime facts')
    for field in ('locks', 'inputs', 'artifacts'):
        values = value.get(field, {})
        if not isinstance(values, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                or not re.fullmatch(r'(?:sha256:)?[0-9a-f]{64}|sha512:[0-9a-f]{128}', v)
                for k, v in values.items()):
            raise ValueError('Environment input/artifact hashes are invalid')
    return json.loads(encoded(value))


def tree_hash(root, limits=ArchiveLimits()):
    """Bind paths, normalized modes and bytes; links/specials never qualify."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or stat.S_IMODE(root.stat().st_mode) != 0o555:
        raise ValueError('Environment dependency root changed')
    digest, count, size = hashlib.sha256(), 0, 0
    for path in sorted(root.rglob('*')):
        count += 1
        if count > limits.entries:
            raise ValueError('Environment tree entry limit exceeded')
        name = path.relative_to(root).as_posix()
        if len(name.encode()) > limits.path_bytes:
            raise ValueError('Environment tree path limit exceeded')
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode) and mode == 0o555:
            record = [name, 'directory', mode]
        elif stat.S_ISREG(info.st_mode) and mode in (0o444, 0o555):
            size += info.st_size
            if size > limits.expanded_bytes:
                raise ValueError('Environment tree byte limit exceeded')
            content = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(65536), b''):
                    content.update(chunk)
            record = [name, 'file', mode, info.st_size, content.hexdigest()]
        else:
            raise ValueError('Environment tree mode, link or file type changed')
        digest.update(encoded(record))
    return digest.hexdigest()


def discard(path):
    """Remove only a caller-owned private staging tree, including frozen modes."""
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError('Refusing to clean an unexpected environment staging path')
    for directory, children, _ in os.walk(path, followlinks=False):
        Path(directory).chmod(0o700)
        for name in children:
            child = Path(directory) / name
            if not child.is_symlink():
                child.chmod(0o700)
    shutil.rmtree(path)


@dataclass(frozen=True)
class Environment:
    id: str
    receipt_hash: str
    dependencies: Path
    image: str
    profile: str
    runtime: dict
    store: Path


class EnvironmentStore:
    def __init__(self, root):
        self.root = Path(root).absolute()
        if any(path.is_symlink() for path in (self.root, *self.root.parents)):
            raise ValueError('Environment store cannot use symlinks')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_uid != os.getuid() or self.root.stat().st_mode & 0o077:
            raise ValueError('Environment store must be controller-owned with mode 0700')

    @contextmanager
    def locked(self, *, shared=False):
        with (self.root / '.lock').open('a') as lock:
            try:
                fcntl.flock(lock, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('Another environment preparation owns this store') from None
            yield

    def remove_private_staging(self):
        with self.locked():
            self._remove_private_staging()

    def _remove_private_staging(self):
        for path in self.root.glob('.prepare-*'):
            discard(path)

    def publish(self, stream, metadata, verify, *, cancelled=lambda: False):
        """Trusted preparer seam: validate, smoke, fence cancellation, then publish."""
        metadata = metadata_checked(metadata)
        def active():
            if cancelled():
                raise ValueError('Environment preparation cancelled before publication')
        with self.locked():
            active()
            self._remove_private_staging()
            stage = Path(tempfile.mkdtemp(prefix='.prepare-', dir=self.root))
            published, committed = None, False
            try:
                limits = limits_for(metadata['profile'])
                dependencies = unpack_archive(stream, stage / 'deps', limits)
                for path in dependencies.rglob('*'):
                    if path.is_dir():
                        path.chmod(0o555)
                dependencies.chmod(0o555)
                before = tree_hash(dependencies, limits)
                active()
                checks = verify(dependencies)
                active()
                if not isinstance(checks, dict) or checks.get('passed') is not True:
                    raise ValueError('Environment offline smoke checks failed')
                if tree_hash(dependencies, limits) != before:
                    raise ValueError('Environment dependencies changed during smoke checks')
                receipt = encoded({'format': 1, 'metadata': metadata,
                                   'tree_sha256': before, 'checks': checks})
                identifier = hashlib.sha256(receipt).hexdigest()
                path = stage / 'receipt.json'
                with path.open('xb') as output:
                    output.write(receipt); output.flush(); os.fsync(output.fileno())
                path.chmod(0o444)
                pending = stage / 'pending'
                with pending.open('xb') as output:
                    output.write(b'Uncommitted environment preparation\n')
                    output.flush(); os.fsync(output.fileno())
                with self._directory_fd(stage) as directory:
                    os.fsync(directory)
                active()
                destination = self.root / identifier
                if os.path.lexists(destination):
                    return self._resolve(identifier, identifier)
                stage.rename(destination)
                published = destination
                with self._directory_fd() as directory:
                    os.fsync(directory)
                result = self._resolve(identifier, identifier, allow_pending=True)
                active()
                (destination / 'pending').unlink()  # Final publication commit.
                committed = True
                published = None  # Commit is durable and verified before releasing readers.
                return result
            except BaseException:
                if published is not None:
                    # Retire first: even failed recursive cleanup leaves no
                    # addressable receipt from this failed publication.
                    published.rename(stage)
                raise
            finally:
                if not committed and stage.exists():
                    discard(stage)

    @contextmanager
    def _directory_fd(self, path=None):
        descriptor = os.open(self.root if path is None else path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            yield descriptor
        finally:
            os.close(descriptor)

    def resolve(self, identifier, expected_hash=None):
        with self.locked(shared=True):
            return self._resolve(identifier, expected_hash)

    def _resolve(self, identifier, expected_hash=None, *, allow_pending=False):
        if not isinstance(identifier, str) or not HEX.fullmatch(identifier):
            raise ValueError('Environment ID must be a receipt SHA-256, never a path')
        root = self.root / identifier
        if not allow_pending and os.path.lexists(root / 'pending'):
            raise ValueError('Environment publication is pending; failed preparation cannot be reused')
        receipt = root / 'receipt.json'
        if root.exists() and (root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode) != 0o700):
            raise ValueError('Environment publication directory ownership or mode changed')
        if root.is_symlink() or receipt.is_symlink() or not receipt.is_file():
            raise ValueError('Environment receipt missing or replaced by a link')
        if receipt.stat().st_size > 65536 or stat.S_IMODE(receipt.stat().st_mode) != 0o444:
            raise ValueError('Environment receipt size or mode changed')
        raw = receipt.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != identifier or (expected_hash is not None and digest != expected_hash):
            raise ValueError('Environment receipt hash changed')
        try:
            value = json.loads(raw)
            metadata = metadata_checked(value['metadata'])
            if type(value['format']) is not int or value['format'] != 1 or value['checks']['passed'] is not True:
                raise ValueError('Environment receipt did not pass checks')
            if tree_hash(root / 'deps', limits_for(metadata['profile'])) != value['tree_sha256']:
                raise ValueError('Environment dependency tree changed')
        except (KeyError, TypeError, OSError, json.JSONDecodeError) as error:
            raise ValueError('Environment receipt or tree is invalid') from error
        return Environment(identifier, digest, root / 'deps', metadata['image'],
                           metadata['profile'], metadata['runtime'], self.root)


def binding(environment):
    checked = EnvironmentStore(environment.store).resolve(environment.id, environment.receipt_hash)
    return {'id': checked.id, 'receipt_sha256': checked.receipt_hash, 'store': str(checked.store),
            'image': checked.image, 'profile': checked.profile, 'runtime': checked.runtime}


def resolve_binding(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('Invalid frozen environment binding')
    try:
        environment = EnvironmentStore(value['store']).resolve(value['id'], value['receipt_sha256'])
        if binding(environment) != value:
            raise ValueError('Frozen environment facts do not match its receipt')
        return environment
    except (KeyError, TypeError) as error:
        raise ValueError('Incomplete frozen environment binding') from error


def runtime_context(task):
    value = task.get('environment')
    if value is None:
        return 'Execution environment: legacy-unbound (runtime was not frozen).'
    usage = {'python-stdlib': 'Python standard library only.',
             'python-api': 'Dependencies are at /opt/deps via PYTHONPATH. Build your project wheel with pip wheel --no-index --no-deps --no-build-isolation; install it with pip install --no-index --no-deps --target /tmp/installed and include that path in PYTHONPATH for tests. Acceptance builds a separate offline wheel.',
             'node-ts': 'Dependencies are at /node_modules. Invoke node /node_modules/typescript/bin/tsc explicitly; no npm download or install is needed.',
             'python-project': 'Project dependencies resolved from its manifests, plus pytest, are at /opt/deps via PYTHONPATH. Run tests with python -m pytest -p no:cacheprovider. Nothing can be installed; do not add dependencies.'}
    project = ('\nProject test command (also run by acceptance): ' + json.dumps(task['test_command'])) if task.get('test_command') else ''
    return usage[value['profile']] + project + '\nFrozen execution environment: ' + json.dumps(
        {key: value[key] for key in ('profile', 'image', 'runtime')}, sort_keys=True)
