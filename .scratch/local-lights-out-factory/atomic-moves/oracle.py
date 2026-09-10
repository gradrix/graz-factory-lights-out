"""Independent real-SQLite invariants; no replacement database or connection."""
import sqlite3
import tempfile
from pathlib import Path
from game_server.state import recorderdb
from common.models.move import Move


class ObservedLock:
    def __init__(self, actual):
        self.actual = actual
        self.held = False

    def __enter__(self):
        self.actual.acquire()
        self.held = True
        return self

    def __exit__(self, *args):
        self.held = False
        self.actual.release()


with tempfile.TemporaryDirectory() as directory:
    recorderdb.RECORDER_DB = str(Path(directory) / 'records.db')
    db = recorderdb.RecorderDb()
    db.lock = ObservedLock(db.lock)
    statements = []
    db.conn.set_trace_callback(lambda sql: statements.append((sql.upper(), db.lock.held)))
    with sqlite3.connect(recorderdb.RECORDER_DB) as reader:
        for size in (0, 1, 2, 7):
            moves = [Move(0, 17, 31, 99-i, 'M'+str(i), 700+i) for i in range(size)]
            before = reader.execute('SELECT * FROM moves ORDER BY id').fetchall()
            assert db.addMoves(moves) is True
            assert not db.conn.in_transaction
            after = reader.execute('SELECT * FROM moves ORDER BY id').fetchall()
            assert after[:len(before)] == before
            assert [row[1:6] for row in after[len(before):]] == [(17,31,i,'M'+str(i),700+i) for i in range(size)]
        for bad_index in (0, 1, 4):
            for field in ('gameid', 'playerid', 'move', 'date'):
                moves = [Move(0, 17, 31, 77, 'new'+str(i), 900+i) for i in range(5)]
                setattr(moves[bad_index], field, None)
                before = reader.execute('SELECT * FROM moves ORDER BY id').fetchall()
                statements.clear()
                result = db.addMoves(moves)
                assert type(result) is int and result == -1
                assert not db.conn.in_transaction, 'failed batch leaves pending transaction'
                assert db.conn.execute('SELECT * FROM moves ORDER BY id').fetchall() == before
                assert reader.execute('SELECT * FROM moves ORDER BY id').fetchall() == before
                transaction_end = [held for sql, held in statements if sql.startswith('ROLLBACK')]
                assert transaction_end and all(transaction_end), 'rollback must finish while writer lock is held'
                assert db.createPlayer('later-'+field+str(bad_index)) != -1
                assert reader.execute('SELECT * FROM moves ORDER BY id').fetchall() == before
                assert db.addMoves([Move(0,17,31,88,'recovery',1234)]) is True
                assert reader.execute('SELECT move FROM moves ORDER BY id DESC LIMIT 1').fetchone() == ('recovery',)
    db.conn.close()
print('atomic-moves-qualified')
