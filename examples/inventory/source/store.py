"""Small SQLite inventory store."""
import sqlite3


def initialize(path):
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS stock (sku TEXT PRIMARY KEY, quantity INTEGER NOT NULL)')


def put(path, sku, quantity):
    with sqlite3.connect(path) as db:
        db.execute('INSERT OR REPLACE INTO stock VALUES (?, ?)', (sku, quantity))


def available(path, sku):
    with sqlite3.connect(path) as db:
        row = db.execute('SELECT quantity FROM stock WHERE sku=?', (sku,)).fetchone()
        return None if row is None else row[0]
