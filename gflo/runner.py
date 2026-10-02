"""Durable task, attempt and acceptance ownership."""
from contextlib import contextmanager
import fcntl
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import tarfile
import uuid

from .observe import Execution, event, identity, redact, schema


def save(path, value):
    """Publish complete JSON or leave the previous artifact intact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def fingerprint(root):
    """Hash relative names, modes and content; never follow workspace links."""
    digest = hashlib.sha256()
    for path in sorted(Path(root).rglob('*')):
        relative = str(path.relative_to(root))
        digest.update(relative.encode() + b'\0')
        if path.is_symlink():
            digest.update(b'link\0' + os.readlink(path).encode())
        elif path.is_file():
            digest.update(str(path.stat().st_mode & 0o777).encode() + b'\0')
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1048576), b''):
                    digest.update(chunk)
        elif not path.is_dir():
            raise ValueError('Unsupported workspace file: ' + relative)
    return digest.hexdigest()


def git(repo, *args, **kwargs):
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          capture_output=True, **kwargs).stdout


class Factory:
    def __init__(self, state, worker, verifier, cleanup=None):
        self.state = Path(state).resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        self.worker = worker
        self.verifier = verifier
        self.cleanup = cleanup
        self.db = sqlite3.connect(self.state / 'state.sqlite')
        self.report = lambda *a, **kw: None
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL,
                contract_hash TEXT NOT NULL, message TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS attempts (
                run_id TEXT NOT NULL, number INTEGER NOT NULL, status TEXT NOT NULL,
                PRIMARY KEY (run_id, number));
        ''')

        schema(self.db)

    @contextmanager
    def locked(self):
        with (self.state / 'runner.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another factory run is active in this state directory') from None
            yield

    def create(self, task_file):
        with self.locked():
            return self._create(Path(task_file).resolve())

    def _create(self, task_file):
        task = json.loads(task_file.read_text())
        if not isinstance(task.get('objective'), str) or not task['objective'].strip():
            raise ValueError('Task needs a nonempty objective')
        checks = task.get('checks')
        if not isinstance(checks, list) or not checks or any(
            not isinstance(c, list) or not c or any(not isinstance(x, str) for x in c)
            for c in checks
        ):
            raise ValueError('checks must be a nonempty list of command argument lists')
        for key, default, upper in [('max_attempts', 3, 10), ('max_turns', 24, 100)]:
            task.setdefault(key, default)
            if type(task[key]) is not int or not 1 <= task[key] <= upper:
                raise ValueError(f'{key} must be between 1 and {upper}')
        repo = (task_file.parent / task['repo']).resolve()
        acceptance = (task_file.parent / task['acceptance']).resolve()
        if not acceptance.is_dir() or not any(acceptance.iterdir()):
            raise ValueError('acceptance must name a nonempty directory')
        if any(p.is_symlink() for p in acceptance.rglob('*')):
            raise ValueError('Acceptance symlinks are unsupported')
        if git(repo, 'status', '--porcelain').strip():
            raise ValueError('Source repository must be clean; commit intended input first')
        if b'160000 ' in git(repo, 'ls-files', '--stage'):
            raise ValueError('Submodules are unsupported in the initial Python profile')
        commit = git(repo, 'rev-parse', 'HEAD', text=True).strip()
        run_id = uuid.uuid4().hex[:12]
        root = self.state / run_id
        root.mkdir()
        workspace = root / 'workspace'
        workspace.mkdir()
        archive = git(repo, 'archive', commit)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar:
                path = workspace / member.name
                if not path.resolve().is_relative_to(workspace):
                    raise ValueError('Unsafe archive path')
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(tar.extractfile(member).read())
                    path.chmod(member.mode & 0o777)
                else:
                    raise ValueError('Only regular files and directories are supported')
        shutil.copytree(acceptance, root / 'acceptance')
        task.update(repo=str(repo), base_commit=commit,
                    acceptance_hash=fingerprint(root / 'acceptance'))
        save(root / 'task.json', task)
        contract_hash = hashlib.sha256((root / 'task.json').read_bytes()).hexdigest()
        # Private Git metadata never enters a worker mount.
        git(root, 'init', '--bare', 'snapshot.git')
        self._index(root, workspace)
        tree = self._snapshot_git(root, 'write-tree').decode().strip()
        save(root / 'base.json', {'tree': tree})
        with self.db:
            self.db.execute('INSERT INTO runs VALUES (?, ?, 0, ?, ?)',
                            (run_id, 'pending', contract_hash, ''))
            event(self.db, run_id, 'created')
        return run_id

    def _snapshot_git(self, root, *args):
        return subprocess.run(['git', '--git-dir', str(root / 'snapshot.git'), *args],
                              check=True, capture_output=True).stdout

    def _index(self, root, workspace):
        self._snapshot_git(root, '--work-tree', str(workspace), 'add', '--all', '--force', '.')

    def status(self, run_id=None):
        if run_id is None:
            return [self.status(row['id']) for row in self.db.execute('SELECT id FROM runs ORDER BY rowid DESC').fetchall()]
        row = self.db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise ValueError('Unknown run: ' + run_id)
        result = dict(row)
        root = self.state / run_id
        if result['status'] == 'accepted':
            try:
                receipt = json.loads((root / 'accepted.json').read_text())
                current = fingerprint(root / 'workspace')
                patch = hashlib.sha256((root / 'change.patch').read_bytes()).hexdigest()
                task_hash = hashlib.sha256((root / 'task.json').read_bytes()).hexdigest()
                if current != receipt['candidate'] or patch != receipt['patch_sha256'] or task_hash != result['contract_hash']:
                    raise ValueError('Accepted artifacts changed')
            except (OSError, ValueError, KeyError):
                result.update(status='invalidated', message='Accepted artifacts changed or are missing; start a new run')
        result.update(directory=str(root), workspace=str(root / 'workspace'),
                      patch=str(root / 'change.patch'))
        return result

    def _state(self, run_id, status, message=''):
        with self.db:
            self.db.execute('UPDATE runs SET status=?, message=? WHERE id=?', (status, redact(message), run_id))
            event(self.db, run_id, status)

    def _finish(self, root, run_id, number, verdict):
        self._index(root, root / 'workspace')
        tree = json.loads((root / 'base.json').read_text())['tree']
        patch = self._snapshot_git(root, 'diff', '--cached', '--binary', tree, '--')
        (root / 'change.patch').write_bytes(patch)
        passed = verdict.get('passed') is True
        if passed:
            save(root / 'accepted.json', {'candidate': verdict['candidate'],
                                         'patch_sha256': hashlib.sha256(patch).hexdigest()})
        with self.db:
            self.db.execute('UPDATE runs SET message=message WHERE id=?', (run_id,))
            control = self.db.execute('SELECT cancel_requested FROM execution WHERE run_id=?', (run_id,)).fetchone()
            if control and control[0]:
                raise KeyboardInterrupt('Cancellation requested')
            event(self.db, run_id, 'accepted' if passed else 'check_failed', attempt=number)
            self.db.execute('UPDATE attempts SET status=? WHERE run_id=? AND number=?',
                            ('passed' if passed else 'failed', run_id, number))
            self.db.execute('UPDATE runs SET status=?, message=? WHERE id=?',
                            ('accepted' if passed else 'repairing', '' if passed else 'Acceptance failed', run_id))
        return passed

    def cancel(self, run_id):
        self.status(run_id)
        with self.db:
            self.db.execute('UPDATE runs SET message=message WHERE id=?', (run_id,))
            row = self.db.execute('SELECT status FROM runs WHERE id=?', (run_id,)).fetchone()
            if row['status'] in ('accepted', 'exhausted'):
                return self.status(run_id)
            control = self.db.execute('SELECT * FROM execution WHERE run_id=?', (run_id,)).fetchone()
            self.db.execute('UPDATE execution SET cancel_requested=1 WHERE run_id=?', (run_id,))
            event(self.db, run_id, 'cancel_requested')
            alive = control and control['pid'] and identity(control['pid']) == control['identity']
            if not alive:
                self.db.execute("UPDATE runs SET status='cancelled' WHERE id=?", (run_id,))
        if alive:
            try:
                fd = os.pidfd_open(control['pid'])
                try:
                    if identity(control['pid']) == control['identity']:
                        signal.pidfd_send_signal(fd, signal.SIGINT)
                finally:
                    os.close(fd)
            except ProcessLookupError:
                pass
        return self.status(run_id)

    def resume(self, run_id):
        with self.locked():
            row = self.status(run_id)
            if row['status'] in ('accepted', 'exhausted'):
                return row
            with Execution(self.state, run_id) as execution:
                self.report = execution.emit
                setter = getattr(self.worker, 'set_observer', None)
                if setter:
                    setter(execution.emit)
                try:
                    return self._resume(run_id)
                finally:
                    self.report = lambda *a, **kw: None
                    if setter:
                        setter(self.report)

    def _resume(self, run_id):
        self.status(run_id)  # Validate the id before resolving any workspace path.
        root = self.state / run_id
        if self.cleanup:
            self.cleanup(root / 'workspace')
        row = self.status(run_id)
        if row['status'] == 'invalidated':
            raise ValueError(row['message'])
        task_path = root / 'task.json'
        if hashlib.sha256(task_path.read_bytes()).hexdigest() != row['contract_hash']:
            raise ValueError('Frozen task contract was modified')
        task = json.loads(task_path.read_text())
        if fingerprint(root / 'acceptance') != task['acceptance_hash']:
            raise ValueError('Frozen acceptance files were modified')
        if row['status'] in ('accepted', 'exhausted'):
            return row
        workspace = root / 'workspace'
        previous = None
        if row['attempts']:
            last = root / 'attempts' / str(row['attempts'])
            record = last / 'verification.json'
            if record.exists():
                previous = json.loads(record.read_text())
                if previous.get('candidate') != fingerprint(workspace):
                    raise ValueError('Workspace changed after verification; start a new run')
                if self._finish(root, run_id, row['attempts'], previous):
                    return self.status(run_id)
            else:
                previous = {'passed': False, 'error': 'Previous attempt interrupted before verification. Inspect retained workspace and finish the task.'}
                with self.db:
                    self.db.execute('UPDATE attempts SET status=? WHERE run_id=? AND number=?',
                                    ('interrupted', run_id, row['attempts']))
        for number in range(row['attempts'] + 1, task['max_attempts'] + 1):
            attempt = root / 'attempts' / str(number)
            attempt.mkdir(parents=True, exist_ok=True)
            save(attempt / 'input.json', {'previous': previous, 'candidate': fingerprint(workspace)})
            with self.db:
                self.db.execute('INSERT INTO attempts VALUES (?, ?, ?)', (run_id, number, 'running'))
                self.db.execute('UPDATE runs SET status=?, attempts=?, message=? WHERE id=?',
                                ('running', number, '', run_id))
            try:
                self.report('working', attempt=number, max_attempts=task['max_attempts'])
                result = self.worker(workspace, task, previous, number)
                save(attempt / 'worker.json', result)
                logging.info("Attempt %s: verifying candidate", number)
                self.report('verifying', attempt=number)
                verdict = self.verifier(workspace, task, root / 'acceptance')
                verdict['candidate'] = fingerprint(workspace)
                save(attempt / 'verification.json', verdict)
                if self._finish(root, run_id, number, verdict):
                    return self.status(run_id)
                previous = verdict
            except (Exception, KeyboardInterrupt) as error:
                save(attempt / 'interruption.json', {'error': str(error), 'type': type(error).__name__})
                control = self.db.execute('SELECT cancel_requested FROM execution WHERE run_id=?', (run_id,)).fetchone()
                self._state(run_id, 'cancelled' if control and control[0] else 'interrupted', str(error) or 'Interrupted')
                raise
        self._state(run_id, 'exhausted', 'Acceptance failed or work interrupted within the attempt budget')
        return self.status(run_id)
