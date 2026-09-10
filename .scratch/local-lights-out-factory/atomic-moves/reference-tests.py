import sqlite3
import pytest
from game_server.state import recorderdb
from common.models.move import Move

@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(recorderdb, 'RECORDER_DB', str(tmp_path / 'records.db'))
    instance = recorderdb.RecorderDb()
    yield instance
    instance.conn.close()


def batch():
    return [Move(0, 8, 3, 91, 'one', 111), Move(0, 8, 3, 92, 'two', 222)]


def test_success_fields_and_commit(db):
    assert db.addMoves(batch()) is True
    assert not db.conn.in_transaction
    with sqlite3.connect(recorderdb.RECORDER_DB) as reader:
        assert reader.execute('SELECT gameid,playerid,idx,move,date FROM moves ORDER BY id').fetchall() == [(8,3,0,'one',111),(8,3,1,'two',222)]


def test_failure_rolls_back_and_recovers(db):
    moves = batch()
    moves[1].move = None
    assert db.addMoves(moves) == -1
    assert not db.conn.in_transaction
    db.createPlayer('later')
    assert db.conn.execute('SELECT move FROM moves').fetchall() == []
    assert db.addMoves(batch()) is True
    assert db.conn.execute('SELECT count(*) FROM moves').fetchone() == (2,)


def test_failure_preserves_committed_rows(db):
    assert db.addMoves(batch()) is True
    before = db.conn.execute('SELECT * FROM moves').fetchall()
    bad = batch()
    bad[1].move = None
    assert db.addMoves(bad) == -1
    assert db.conn.execute('SELECT * FROM moves').fetchall() == before


def test_empty_is_success(db):
    assert db.addMoves([]) is True
    assert not db.conn.in_transaction
    assert db.conn.execute('SELECT * FROM moves').fetchall() == []


def test_first_row_failure(db):
    bad = batch()
    bad[0].date = None
    assert db.addMoves(bad) == -1
    assert not db.conn.in_transaction
    assert db.conn.execute('SELECT * FROM moves').fetchall() == []
