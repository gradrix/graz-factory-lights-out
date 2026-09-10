"""Real deferred foreign-key failure exercises commit-time rollback and recovery."""
import sqlite3
import tempfile
from pathlib import Path
from game_server.state import recorderdb
from common.models.move import Move

with tempfile.TemporaryDirectory() as directory:
    recorderdb.RECORDER_DB = str(Path(directory) / 'records.db')
    db = recorderdb.RecorderDb()
    db.conn.execute('PRAGMA foreign_keys=ON')
    player = db.createPlayer('existing')
    game = db.createGame()
    assert db.addMoves([Move(0,game.id,player.id,90,'existing',1)]) is True
    before = db.conn.execute('SELECT * FROM moves').fetchall()
    # Inserts succeed; the deferred foreign-key violation is raised only at COMMIT.
    db.conn.execute('PRAGMA defer_foreign_keys=ON')
    sql = []
    db.conn.set_trace_callback(sql.append)
    assert db.addMoves([Move(0,game.id,player.id,91,'partial',2),Move(0,999999,player.id,92,'invalid',3)]) == -1
    assert 'COMMIT' in sql and 'ROLLBACK' in sql, sql
    assert not db.conn.in_transaction
    assert db.conn.execute('SELECT * FROM moves').fetchall() == before
    assert db.createPlayer('after-failure') != -1
    with sqlite3.connect(recorderdb.RECORDER_DB) as reader:
        assert reader.execute('SELECT * FROM moves').fetchall() == before
        assert db.addMoves([Move(0,game.id,player.id,93,'recovered',4)]) is True
        assert reader.execute('SELECT move FROM moves ORDER BY id').fetchall() == [('existing',),('recovered',)]
    db.conn.close()
print('deferred-commit-recovery-qualified')
