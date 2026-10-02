"""Durable execution events and read-only views. Linux process identity fences PIDs."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time


def identity(pid):
    try:
        stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        if stat[0] == 'Z':
            return None
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip() + ':' + stat[19]
    except (OSError, IndexError):
        return None


def redact(text):
    text = re.sub(r'(?i)(bearer\s+)[\w.\-]+', r'\1[redacted]', text)
    return re.sub(r'(?i)((?:api[_-]?key|password|secret|token)["\s]*[:=]\s*["\']?)[^\s,"\'}]+', r'\1[redacted]', text)


def schema(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
            time REAL NOT NULL, version INTEGER NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS event_run ON events(run_id,seq);
        CREATE TABLE IF NOT EXISTS execution (
            run_id TEXT PRIMARY KEY, pid INTEGER, identity TEXT, heartbeat REAL,
            phase TEXT NOT NULL, action_at REAL NOT NULL, detail TEXT NOT NULL,
            cancel_requested INTEGER NOT NULL DEFAULT 0);
    ''')


def event(db, run, kind, **data):
    data = json.dumps(data)
    if len(data) > 4096:
        raise ValueError('Event metadata exceeds 4096 characters')
    db.execute('INSERT INTO events(run_id,time,version,kind,data) VALUES(?,?,1,?,?)',
               (run, time.time(), kind, redact(data)))


class Execution:
    def __init__(self, state, run):
        self.state, self.run = Path(state), run
        self.db = sqlite3.connect(self.state / 'state.sqlite', timeout=10)
        self.stop = threading.Event()

    def __enter__(self):
        now = time.time()
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO execution VALUES(?,?,?,?,?,?,?,0)',
                            (self.run, os.getpid(), identity(os.getpid()), now, 'starting', now, '{}'))
            event(self.db, self.run, 'resumed')
        def beat():
            db = sqlite3.connect(self.state / 'state.sqlite', timeout=10)
            try:
                while not self.stop.wait(1):
                    with db:
                        db.execute('UPDATE execution SET heartbeat=? WHERE run_id=?', (time.time(), self.run))
            finally:
                db.close()
        self.thread = threading.Thread(target=beat, daemon=True)
        self.thread.start()
        return self

    def emit(self, phase, **data):
        with self.db:
            self.db.execute('UPDATE execution SET phase=?,action_at=?,detail=? WHERE run_id=?',
                            (phase, time.time(), json.dumps(data), self.run))
            event(self.db, self.run, phase, **data)

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()
        with self.db:
            self.db.execute('UPDATE execution SET pid=NULL,identity=NULL WHERE run_id=?', (self.run,))
        self.db.close()


class Observer:
    def __init__(self, state):
        self.state = Path(state).resolve()

    @contextmanager
    def connect(self):
        db = sqlite3.connect((self.state / 'state.sqlite').as_uri() + '?mode=ro', uri=True)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def status(self, run=None):
        from .runner import accepted_intact
        if run is None and not (self.state / 'state.sqlite').exists():
            return []
        with self.connect() as db:
            if run is None:
                return [self.status(r['id']) for r in db.execute('SELECT id FROM runs ORDER BY rowid DESC LIMIT 100')]
            row = db.execute('SELECT * FROM runs WHERE id=?', (run,)).fetchone()
            if row is None:
                raise ValueError('Unknown run')
            result = dict(row)
            execution = db.execute('SELECT * FROM execution WHERE run_id=?', (run,)).fetchone()
        root = self.state / run
        task = json.loads((root / 'task.json').read_text())
        result['budget'] = {k: task[k] for k in ('max_attempts', 'max_turns')}
        result['owner_alive'] = False
        result['phase'] = result['status']
        if execution:
            execution = dict(execution)
            alive = bool(execution['pid'] and identity(execution['pid']) == execution['identity'])
            result.update(owner_alive=alive, heartbeat=execution['heartbeat'],
                          heartbeat_age_s=round(time.time() - execution['heartbeat'], 1),
                          phase=execution['phase'], last_action_at=execution['action_at'],
                          action_age_s=round(time.time() - execution['action_at'], 1),
                          detail=json.loads(execution['detail']), cancel_requested=bool(execution['cancel_requested']))
            if not alive and (result['status'] in ('running', 'repairing') or (result['status'] == 'pending' and execution['pid'])):
                result.update(status='cancelled' if execution['cancel_requested'] else 'interrupted', phase='interrupted', message='Runner process ended; resume to recover retained work')
            result['waiting_on_model'] = alive and result['phase'] in ('model_wait', 'review_wait')
            # Elapsed silence is observable; it is not proof that inference is deadlocked.
            result['model_slow'] = result['waiting_on_model'] and result['action_age_s'] >= 30
        if result['status'] == 'accepted' and not accepted_intact(root, result['contract_hash'], result['attempts']):
            result.update(status='invalidated', phase='invalidated', message='Accepted artifacts changed or are missing')
        if result['status'] in ('accepted', 'exhausted', 'cancelled', 'interrupted', 'invalidated', 'needs_input'):
            result['phase'] = result['status']
        result['message'] = redact(result['message'])
        result['artifacts'] = [str(p.relative_to(root)) for p in sorted(root.rglob('*'))
                               if p.is_file() and self.allowed(str(p.relative_to(root)))]
        return result

    def events(self, run, after=0):
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM runs WHERE id=?', (run,)).fetchone():
                raise ValueError('Unknown run')
            return [dict(r, data=json.loads(r['data'])) for r in db.execute(
                'SELECT * FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT 500', (run, after))]

    @staticmethod
    def allowed(name):
        return bool(re.fullmatch(r'(change\.patch|accepted\.json|attempts/[1-9][0-9]*/(verification|worker|interruption|review)\.json)', name))

    def artifact(self, run, name):
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM runs WHERE id=?', (run,)).fetchone():
                raise ValueError('Unknown run')
        root = self.state / run
        path = root / name
        if not self.allowed(name) or any(p.is_symlink() for p in [path, *path.parents]) or not path.is_file():
            raise ValueError('Artifact unavailable')
        with path.open('rb') as stream:
            content = stream.read(1024 * 1024 + 1)
        truncated = len(content) > 1024 * 1024
        return redact(content[:1024 * 1024].decode(errors='replace')) + ('\n[truncated at 1 MiB]' if truncated else '')
