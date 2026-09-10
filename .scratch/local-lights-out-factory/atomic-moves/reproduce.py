"""Run against a checkout: a failed batch must not leak into a later commit."""
import os
from pathlib import Path
import sys
import tempfile

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
os.chdir(root)
from game_server.state import recorderdb
from common.models.move import Move

with tempfile.TemporaryDirectory() as directory:
    recorderdb.RECORDER_DB = str(Path(directory) / "records.db")
    db = recorderdb.RecorderDb()
    assert db.addMoves([Move(0, 1, 1, 7, "valid", 123), Move(0, 1, 1, 8, None, 124)]) == -1
    pending = db.conn.in_transaction
    db.createPlayer("later-write")
    rows = db.conn.execute("SELECT move FROM moves").fetchall()
    print(dict(pending_after_failure=pending, moves_after_later_commit=rows))
    assert rows == [], "Failed batch leaked into a subsequent committed write"
    db.conn.close()
