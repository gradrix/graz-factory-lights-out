def legacy(p):
 import sqlite3
 con=sqlite3.connect(p['db'])
 try:return [{'sku':s,'quantity':q} for s,q in sorted(con.execute('SELECT sku,quantity FROM stock').fetchall())]
 finally:con.close()

def feature(p):
 import sqlite3
 con=sqlite3.connect(p['db'])
 try:
  with con:
   for item in p['changes']:
    row=con.execute('SELECT quantity FROM stock WHERE sku=?',(item['sku'],)).fetchone()
    if row is None or row[0]+item['delta']<0:raise ValueError('invalid adjustment')
    con.execute('UPDATE stock SET quantity=? WHERE sku=?',(row[0]+item['delta'],item['sku']))
  return legacy(p)
 finally:con.close()
