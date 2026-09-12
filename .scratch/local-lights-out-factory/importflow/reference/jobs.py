import json
import math
import re
import sqlite3
import uuid
from contextlib import contextmanager


def _clock(value, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError('invalid time')


class Store:
    def __init__(self, path, max_pending=10000):
        if type(max_pending) is not int or max_pending < 1:
            raise ValueError('invalid capacity')
        self.path = str(path)
        self.max_pending = max_pending
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT UNIQUE NOT NULL, key TEXT UNIQUE NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                token TEXT, lease_until REAL, result TEXT, error TEXT)''')
            db.execute('CREATE INDEX IF NOT EXISTS ready ON jobs(status,sequence)')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            yield db
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _record(row):
        if row is None:
            return None
        data = dict(row)
        data.pop('sequence')
        if data['result'] is not None:
            data['result'] = json.loads(data['result'])
        return data

    def submit(self, key, kind, payload):
        for value, pattern in ((key,r'[A-Za-z0-9_-]{1,80}'),(kind,r'[a-z][a-z0-9_]{0,31}'),(payload,r'[0-9a-f]{64}')):
            if not isinstance(value,str) or not re.fullmatch(pattern,value):
                raise ValueError('invalid submission')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM jobs WHERE key=?',(key,)).fetchone()
            if old:
                if old['kind'] != kind or old['payload'] != payload:
                    raise ValueError('idempotency conflict')
                db.commit()
                return self._record(old)
            pending = db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]
            if pending >= self.max_pending:
                raise OverflowError('queue full')
            identity = uuid.uuid4().hex
            db.execute("INSERT INTO jobs(id,key,kind,payload,status) VALUES(?,?,?,?,'queued')",(identity,key,kind,payload))
            row = db.execute('SELECT * FROM jobs WHERE id=?',(identity,)).fetchone()
            db.commit()
            return self._record(row)

    def get(self, job_id):
        with self._db() as db:
            return self._record(db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone())

    def claim(self, now, ttl=30.0):
        _clock(now)
        _clock(ttl,True)
        _clock(now+ttl)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE jobs SET status='failed',error='attempts exhausted',token=NULL,lease_until=NULL WHERE status='running' AND lease_until<=? AND attempts>=3",(now,))
            row = db.execute("SELECT * FROM jobs WHERE status='queued' OR (status='running' AND lease_until<=? AND attempts<3) ORDER BY sequence LIMIT 1",(now,)).fetchone()
            if row is None:
                db.commit()
                return None
            token = uuid.uuid4().hex
            db.execute("UPDATE jobs SET status='running',attempts=attempts+1,token=?,lease_until=? WHERE id=?",(token,now+ttl,row['id']))
            result = db.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone()
            db.commit()
            return self._record(result)

    def finish(self, job_id, token, now, *, result=None, error=None):
        _clock(now)
        if (result is None) == (error is None):
            raise ValueError('exactly one result or error')
        data = None
        if error is not None:
            if not isinstance(error,str) or not 1 <= len(error) <= 2000:
                raise ValueError('invalid error')
        else:
            try:
                data = json.dumps(result,ensure_ascii=False,allow_nan=False)
            except (ValueError,TypeError) as exc:
                raise ValueError('invalid JSON result') from exc
            if len(data.encode()) > 1048576:
                raise ValueError('result too large')
        with self._db() as db:
            changed = db.execute("UPDATE jobs SET status=?,result=?,error=?,token=NULL,lease_until=NULL WHERE id=? AND status='running' AND token=? AND lease_until>?",('failed' if error is not None else 'succeeded',data,error,job_id,token,now)).rowcount
            return changed == 1
