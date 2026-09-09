"""Frozen stateful workload definitions and independent dictionary-state oracle.

REFERENCE is a preflight control only. Workers receive BASE and public contracts.
"""

import json
from textwrap import dedent

REFERENCE = {
    "quantities.py": dedent("""\
        def require_stock(value):
            if type(value) is not int or not 0 <= value <= 1000000000:
                raise ValueError('invalid')
            return value

        def require_quantity(value):
            if type(value) is not int or not 1 <= value <= 1000000000:
                raise ValueError('invalid')
            return value
    """),
    "storage.py": dedent('''\
        import sqlite3

        def connect(path):
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys=ON')
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS items(sku TEXT PRIMARY KEY, stock INTEGER NOT NULL CHECK(stock>=0));
                CREATE TABLE IF NOT EXISTS reservations(request_id TEXT PRIMARY KEY, sku TEXT NOT NULL REFERENCES items(sku), quantity INTEGER NOT NULL CHECK(quantity>0), status TEXT NOT NULL CHECK(status IN ('active','cancelled')));
                CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, request_id TEXT NOT NULL, quantity INTEGER NOT NULL);
            """)
            return conn
    '''),
    "requests.py": dedent("""\
        def existing(conn, request_id, sku, quantity):
            row=conn.execute('SELECT * FROM reservations WHERE request_id=?',(request_id,)).fetchone()
            if row is None:
                return None
            if row['sku'] != sku or row['quantity'] != quantity:
                raise ValueError('invalid')
            return dict(row)
    """),
    "reserve.py": dedent("""\
        from quantities import require_quantity
        from requests import existing

        def reserve(conn, request_id, sku, quantity):
            require_quantity(quantity)
            if type(request_id) is not str or not request_id or type(sku) is not str or not sku:
                raise ValueError('invalid')
            with conn:
                conn.execute('BEGIN IMMEDIATE')
                previous=existing(conn,request_id,sku,quantity)
                if previous is not None:
                    return previous
                row=conn.execute('SELECT stock FROM items WHERE sku=?',(sku,)).fetchone()
                if row is None or row['stock'] < quantity:
                    raise ValueError('invalid')
                conn.execute('UPDATE items SET stock=stock-? WHERE sku=?',(quantity,sku))
                conn.execute("INSERT INTO reservations VALUES(?,?,?,'active')",(request_id,sku,quantity))
                conn.execute("INSERT INTO events(kind,request_id,quantity) VALUES('reserve',?,?)",(request_id,quantity))
            return {'request_id':request_id,'sku':sku,'quantity':quantity,'status':'active'}
    """),
    "cancel.py": dedent("""\
        def cancel(conn, request_id):
            with conn:
                conn.execute('BEGIN IMMEDIATE')
                row=conn.execute('SELECT * FROM reservations WHERE request_id=?',(request_id,)).fetchone()
                if row is None:
                    raise ValueError('invalid')
                if row['status']=='active':
                    conn.execute('UPDATE items SET stock=stock+? WHERE sku=?',(row['quantity'],row['sku']))
                    conn.execute("UPDATE reservations SET status='cancelled' WHERE request_id=?",(request_id,))
                    conn.execute("INSERT INTO events(kind,request_id,quantity) VALUES('cancel',?,?)",(request_id,row['quantity']))
            result=dict(row)
            result['status']='cancelled'
            return result
    """),
    "reports.py": dedent("""\
        from storage import connect

        def summary(path):
            conn=connect(path)
            try:
                available=conn.execute('SELECT COALESCE(SUM(stock),0) FROM items').fetchone()[0]
                reserved=conn.execute("SELECT COALESCE(SUM(quantity),0) FROM reservations WHERE status='active'").fetchone()[0]
                return {'available':available,'reserved':reserved}
            finally:
                conn.close()
    """),
    "audit.py": dedent("""\
        def export(conn):
            return [dict(row) for row in conn.execute('SELECT seq,kind,request_id,quantity FROM events ORDER BY seq')]
    """),
    "cli.py": dedent("""\
        import json,sys,sqlite3
        from storage import connect
        from quantities import require_stock
        from reserve import reserve
        from cancel import cancel
        from reports import summary
        from audit import export

        def main():
            conn=connect(sys.argv[1])
            try:
                x=json.load(sys.stdin)
                if x['op']=='create':
                    stock=require_stock(x['stock']); sku=x['sku']
                    if type(sku) is not str or not sku: raise ValueError('invalid')
                    with conn: conn.execute('INSERT INTO items VALUES(?,?)',(sku,stock))
                    result={'sku':sku,'stock':stock}
                elif x['op']=='reserve': result=reserve(conn,x['request_id'],x['sku'],x['quantity'])
                elif x['op']=='cancel': result=cancel(conn,x['request_id'])
                elif x['op']=='report': result=summary(sys.argv[1])
                elif x['op']=='audit': result=export(conn)
                else: raise ValueError('invalid')
            except (ValueError,KeyError,TypeError,sqlite3.IntegrityError):
                result={'error':'invalid'}
            finally:
                conn.close()
            print(json.dumps(result,sort_keys=True))

        if __name__=='__main__': main()
    """),
}
BASE = REFERENCE | {
    "quantities.py": "def require_stock(value): return value\ndef require_quantity(value): return value\n",
    "storage.py": REFERENCE["storage.py"].replace(
        "sqlite3.connect(path)", 'sqlite3.connect(":memory:")'
    ),
    "requests.py": "def existing(conn,request_id,sku,quantity): return None\n",
    "reserve.py": "def reserve(conn,request_id,sku,quantity): raise NotImplementedError\n",
    "cancel.py": "def cancel(conn,request_id): raise NotImplementedError\n",
    "reports.py": 'def summary(path): return {"available":0,"reserved":0}\n',
    "audit.py": "def export(conn): return []\n",
    "cli.py": 'print("{}")\n',
}
CONTRACT = """Stateful inventory contracts v1. Use only the Python standard library.
quantities.require_stock(x) returns x for exact integers 0..1_000_000_000; require_quantity(x)
returns x for exact integers 1..1_000_000_000. Booleans and all other values raise ValueError.
storage.connect(path) returns an open SQLite connection with sqlite3.Row rows, foreign keys
on and the declared tables. It must preserve committed data across connections/processes.
items(sku TEXT PRIMARY KEY,stock INTEGER NOT NULL CHECK(stock>=0)); reservations(request_id
TEXT PRIMARY KEY,sku TEXT REFERENCES items(sku),quantity INTEGER CHECK(quantity>0),status
TEXT either active or cancelled); events(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,
request_id TEXT,quantity INTEGER). A fresh path creates those tables; existing data survives.
requests.existing(conn,id,sku,q) returns None for an unused ID, a dict with request_id,sku,
quantity,status for the same payload even if cancelled, or raises ValueError for a changed
sku or quantity. reserve.reserve(conn,id,sku,q) returns that record and uses the quantities
and requests helpers. Require nonempty string IDs/SKUs, valid quantity, and enough stock.
A new reservation atomically decrements items.stock, inserts an active reservation and one
reserve event. Replays return the existing record without stock/event changes. Invalid
requests raise ValueError and leave all state unchanged. Transactions must serialize
competing reservations (BEGIN IMMEDIATE). Callers supply an idle connection.
cancel.cancel(conn,id) refunds an active reservation exactly once, marks it cancelled and
adds one cancel event; repeated cancellation returns the cancelled record with no effects.
Unknown IDs raise ValueError. Both operations own and finish their transactions.
reports.summary(path) returns {available:sum(items.stock),reserved:sum(active quantities)};
empty sums are zero. audit.export(conn) returns event dicts with exactly seq, kind, request_id, quantity,
including the seq field in every returned dict, in increasing seq order.
CLI: python cli.py DB_PATH, one JSON object on stdin, one JSON value plus newline on stdout.
Operations: create {sku,stock} -> {sku,stock}; reserve {request_id,sku,quantity} -> reservation
record; cancel {request_id} -> cancelled record; report -> summary; audit -> event list.
Invalid operations/payloads and duplicate SKU creation return {error:"invalid"}. CLI must
use the supplied domain functions; errors must not partially change persistent state.
"""

QUANTITY_DRIVER = """import json,quantities
x=json.load(__import__('sys').stdin); out=[]
for v in x['values']:
 try: out.append({'value':getattr(quantities,x['function'])(v)})
 except ValueError: out.append({'error':'invalid'})
print(json.dumps(out,sort_keys=True))
"""
STORAGE_DRIVER = """import json,storage
connect=getattr(storage,__import__('sys').argv[1])
a=connect('store.db'); a.execute("INSERT INTO items VALUES('A',11)"); a.commit(); a.close()
b=connect('store.db'); row=b.execute("SELECT stock FROM items WHERE sku='A'").fetchone()
print(json.dumps({'stock':None if row is None else row['stock'],'foreign_keys':b.execute('PRAGMA foreign_keys').fetchone()[0],'legacy_present':hasattr(storage,'connect')},sort_keys=True)); b.close()
"""
DIRECT_DRIVER = """import json,sys,storage,reserve,cancel,reports,audit
x=json.load(sys.stdin); c=storage.connect('store.db'); out=[]
for op in x['operations']:
 try:
  if op['op']=='create':
   with c: c.execute('INSERT INTO items VALUES(?,?)',(op['sku'],op['stock']))
   r={'sku':op['sku'],'stock':op['stock']}
  elif op['op']=='reserve': r=reserve.reserve(c,op['request_id'],op['sku'],op['quantity'])
  elif op['op']=='cancel': r=cancel.cancel(c,op['request_id'])
  else: raise ValueError('invalid')
 except ValueError: r={'error':'invalid'}
 out.append(r)
r={'responses':out,'items':[dict(v) for v in c.execute('SELECT * FROM items ORDER BY sku')], 'reservations':[dict(v) for v in c.execute('SELECT * FROM reservations ORDER BY request_id')], 'events':[dict(v) for v in c.execute('SELECT * FROM events ORDER BY seq')]}
if x.get('report'): r['report']=reports.summary('store.db')
if x.get('audit'): r['audit']=audit.export(c)
c.close(); print(json.dumps(r,sort_keys=True))
"""
CLI_DRIVER = """import json,sys,subprocess,sqlite3
out=[]
for op in json.load(sys.stdin):
 p=subprocess.run([sys.executable,'cli.py','store.db'],input=json.dumps(op),text=True,capture_output=True,check=True,timeout=3)
 out.append(json.loads(p.stdout))
c=sqlite3.connect('store.db'); c.row_factory=sqlite3.Row
r={'responses':out,'items':[dict(v) for v in c.execute('SELECT * FROM items ORDER BY sku')], 'reservations':[dict(v) for v in c.execute('SELECT * FROM reservations ORDER BY request_id')], 'events':[dict(v) for v in c.execute('SELECT * FROM events ORDER BY seq')]}
c.close(); print(json.dumps(r,sort_keys=True))
"""
CONCURRENT_DRIVER = """import json,sys,subprocess
subprocess.run([sys.executable,'cli.py','store.db'],input=json.dumps({'op':'create','sku':'A','stock':10}),text=True,capture_output=True,check=True)
children=[]
for identity in ['a','b']:
 p=subprocess.Popen([sys.executable,'cli.py','store.db'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 p.stdin.write(json.dumps({'op':'reserve','request_id':identity,'sku':'A','quantity':6})); p.stdin.close(); children.append(p)
rows=[]
for p in children:
 text=p.stdout.read(); p.wait(timeout=5); rows.append(json.loads(text))
p=subprocess.run([sys.executable,'cli.py','store.db'],input='{"op":"report"}',text=True,capture_output=True,check=True)
print(json.dumps({'active':sum(r.get('status')=='active' for r in rows),'errors':sum(r.get('error')=='invalid' for r in rows),'report':json.loads(p.stdout)},sort_keys=True))
"""


def state_oracle(operations, report=False, audit=False):
    items, reservations, events, responses = {}, {}, [], []

    def valid(v, minimum):
        return type(v) is int and minimum <= v <= 1000000000

    for op in operations:
        try:
            kind = op["op"]
            if kind == "create":
                sku, stock = op["sku"], op["stock"]
                if type(sku) is not str or not sku or sku in items or not valid(stock, 0):
                    raise ValueError
                items[sku] = stock
                result = {"sku": sku, "stock": stock}
            elif kind == "reserve":
                identity, sku, q = op["request_id"], op["sku"], op["quantity"]
                if (
                    type(identity) is not str
                    or not identity
                    or type(sku) is not str
                    or not sku
                    or not valid(q, 1)
                ):
                    raise ValueError
                if identity in reservations:
                    result = reservations[identity]
                    if result["sku"] != sku or result["quantity"] != q:
                        raise ValueError
                else:
                    if sku not in items or items[sku] < q:
                        raise ValueError
                    items[sku] -= q
                    result = {"request_id": identity, "sku": sku, "quantity": q, "status": "active"}
                    reservations[identity] = result
                    events.append(
                        {
                            "seq": len(events) + 1,
                            "kind": "reserve",
                            "request_id": identity,
                            "quantity": q,
                        }
                    )
            elif kind == "cancel":
                identity = op["request_id"]
                if identity not in reservations:
                    raise ValueError
                result = reservations[identity]
                if result["status"] == "active":
                    items[result["sku"]] += result["quantity"]
                    result = result | {"status": "cancelled"}
                    reservations[identity] = result
                    events.append(
                        {
                            "seq": len(events) + 1,
                            "kind": "cancel",
                            "request_id": identity,
                            "quantity": result["quantity"],
                        }
                    )
            elif kind == "report":
                result = {
                    "available": sum(items.values()),
                    "reserved": sum(
                        r["quantity"] for r in reservations.values() if r["status"] == "active"
                    ),
                }
            elif kind == "audit":
                result = events
            else:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            result = {"error": "invalid"}
        responses.append(json.loads(json.dumps(result)))
    result = {
        "responses": responses,
        "items": [{"sku": s, "stock": items[s]} for s in sorted(items)],
        "reservations": [reservations[s] for s in sorted(reservations)],
        "events": events,
    }
    if report:
        result["report"] = {
            "available": sum(items.values()),
            "reserved": sum(
                r["quantity"] for r in reservations.values() if r["status"] == "active"
            ),
        }
    if audit:
        result["audit"] = events
    return result


def operations():
    return [
        {"op": "create", "sku": "A", "stock": 10},
        {"op": "reserve", "request_id": "r1", "sku": "A", "quantity": 3},
        {"op": "reserve", "request_id": "r1", "sku": "A", "quantity": 3},
        {"op": "reserve", "request_id": "r1", "sku": "A", "quantity": 4},
        {"op": "reserve", "request_id": "too-much", "sku": "A", "quantity": 8},
        {"op": "cancel", "request_id": "r1"},
        {"op": "cancel", "request_id": "r1"},
        {"op": "reserve", "request_id": "r1", "sku": "A", "quantity": 3},
        {"op": "reserve", "request_id": "r2", "sku": "A", "quantity": 10},
        {"op": "create", "sku": "B", "stock": 0},
        {"op": "reserve", "request_id": "bad", "sku": "A", "quantity": True},
        {"op": "cancel", "request_id": "missing"},
    ]


def _stage_definitions():
    # (name, writable paths, required source views, objective, command/input/expected cases)
    qty = []
    for function, minimum in [("require_stock", 0), ("require_quantity", 1)]:
        values = [-1, 0, 1, 1000000000, 1000000001, True, False, 1.0, "1", None]
        expected = [
            {"value": v} if type(v) is int and minimum <= v <= 1000000000 else {"error": "invalid"}
            for v in values
        ]
        qty.append(
            (("python", "-c", QUANTITY_DRIVER), {"function": function, "values": values}, expected)
        )
    basic = [
        operations()[0],
        operations()[1],
        operations()[4],
        {"op": "reserve", "request_id": "r2", "sku": "A", "quantity": 2},
    ]
    replay = operations()[:4]
    complete = operations()

    def direct(ops, report=False, audit=False):
        return (
            ("python", "-c", DIRECT_DRIVER),
            {"operations": ops, "report": report, "audit": audit},
            state_oracle(ops, report, audit),
        )

    return [
        (
            "quantities",
            ["quantities.py"],
            ["quantities.py"],
            "Implement the two exact integer validators in quantities.py.",
            qty,
        ),
        (
            "storage",
            ["storage.py"],
            ["storage.py"],
            "Fix storage.connect so committed state persists at the supplied path, preserving the schema and row/foreign-key settings.",
            [
                (
                    ("python", "-c", STORAGE_DRIVER, "connect"),
                    None,
                    {"stock": 11, "foreign_keys": 1, "legacy_present": True},
                )
            ],
        ),
        (
            "reserve",
            ["reserve.py"],
            ["reserve.py", "requests.py", "quantities.py"],
            "Implement atomic reserve() using the quantities and requests helpers and the declared SQLite schema. Use BEGIN IMMEDIATE. Invalid requests must raise ValueError without effects.",
            [
                direct(basic),
                direct(
                    [
                        {"op": "create", "sku": "Z", "stock": 0},
                        {"op": "reserve", "request_id": "x", "sku": "Z", "quantity": 1},
                    ]
                ),
            ],
        ),
        (
            "requests",
            ["requests.py"],
            ["requests.py", "reserve.py"],
            "Implement existing() so exact request replays return the persisted record, including cancelled status, and changed payloads raise ValueError.",
            [direct(replay)],
        ),
        (
            "cancel",
            ["cancel.py"],
            ["cancel.py", "reserve.py"],
            "Implement atomic cancellation, refunding stock and appending a cancel event exactly once. Repeated cancellation returns the same cancelled record.",
            [direct(complete)],
        ),
        (
            "cli",
            ["cli.py"],
            ["cli.py", "storage.py", "quantities.py"],
            "Implement the declared JSON CLI. Use the supplied functions rather than duplicating domain rules. Each invocation is a separate process sharing the path in argv[1].",
            [(("python", "-c", CLI_DRIVER), complete, state_oracle(complete))],
        ),
        (
            "reports",
            ["reports.py"],
            ["reports.py", "storage.py"],
            "Implement summary(path) with persistent aggregate available and active-reserved counts; close its connection.",
            [direct(complete, report=True), direct([], report=True)],
        ),
        (
            "audit",
            ["audit.py"],
            ["audit.py"],
            "Implement export(conn) returning every event as a dict with exactly seq, kind, request_id, quantity. Include seq in each returned dict and order by ascending seq.",
            [direct(complete, audit=True)],
        ),
        (
            "storage-v2",
            ["storage.py"],
            ["storage.py"],
            "Revise the provider API: rename storage.connect(path) to storage.open_database(path), remove the old connect export, preserve all database behavior. Consumers migrate in the next prepared task.",
            [
                (
                    ("python", "-c", STORAGE_DRIVER, "open_database"),
                    None,
                    {"stock": 11, "foreign_keys": 1, "legacy_present": False},
                )
            ],
        ),
        (
            "consumers-v2",
            ["cli.py", "reports.py"],
            ["cli.py", "reports.py", "storage.py"],
            "Migrate both consumers from removed storage.connect to storage.open_database. Preserve every CLI and report behavior; do not add compatibility shims to storage.py. Interface obligations: storage.open_database(path) returns a connection; reports.summary(path) takes the database file path, opens and closes its own connection, and returns available/reserved counts. Preserve this path-based reporting interface at every call site.",
            [
                (
                    ("python", "-c", CLI_DRIVER),
                    complete + [{"op": "report"}, {"op": "audit"}],
                    state_oracle(complete + [{"op": "report"}, {"op": "audit"}]),
                ),
                (
                    ("python", "-c", CONCURRENT_DRIVER),
                    None,
                    {"active": 1, "errors": 1, "report": {"available": 4, "reserved": 6}},
                ),
            ],
        ),
    ]


def steps():
    ordered = {step[0]: step for step in _stage_definitions()}
    command = """import json,storage,requests
c=storage.connect('store.db')
c.execute("INSERT INTO items VALUES('A',7)")
c.execute("INSERT INTO reservations VALUES('active','A',3,'active')")
c.execute("INSERT INTO reservations VALUES('cancelled','A',2,'cancelled')")
c.commit(); out=[]
for args in json.load(__import__('sys').stdin):
 try: out.append(requests.existing(c,*args))
 except ValueError: out.append({'error':'invalid'})
print(json.dumps({'results':out,'stock':c.execute("SELECT stock FROM items WHERE sku='A'").fetchone()[0],'rows':c.execute('SELECT COUNT(*) FROM reservations').fetchone()[0]},sort_keys=True)); c.close()
"""
    given = [
        ["missing", "A", 3],
        ["active", "A", 3],
        ["cancelled", "A", 2],
        ["active", "A", 4],
        ["active", "B", 3],
    ]
    expected = {
        "results": [
            None,
            {"request_id": "active", "sku": "A", "quantity": 3, "status": "active"},
            {"request_id": "cancelled", "sku": "A", "quantity": 2, "status": "cancelled"},
            {"error": "invalid"},
            {"error": "invalid"},
        ],
        "stock": 7,
        "rows": 2,
    }
    name, writable, selected, objective, old_cases = ordered["requests"]
    ordered["requests"] = (
        name,
        writable,
        ["requests.py", "storage.py"],
        objective,
        [(("python", "-c", command), given, expected)],
    )
    return [
        ordered[name]
        for name in (
            "quantities",
            "storage",
            "requests",
            "reserve",
            "cancel",
            "reports",
            "audit",
            "cli",
            "storage-v2",
            "consumers-v2",
        )
    ]


def reference_update(name, paths):
    result = {p: REFERENCE[p] for p in paths}
    if name == "storage-v2":
        result["storage.py"] = result["storage.py"].replace(
            "def connect(path):", "def open_database(path):"
        )
    if name == "consumers-v2":
        result = {
            p: s.replace(
                "from storage import connect", "from storage import open_database as connect"
            )
            for p, s in result.items()
        }
    return result
