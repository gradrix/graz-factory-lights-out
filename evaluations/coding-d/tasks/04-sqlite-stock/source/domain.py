def legacy(p):
 import sqlite3
 con=sqlite3.connect(p['db'])
 try:return [{'sku':s,'quantity':q} for s,q in sorted(con.execute('SELECT sku,quantity FROM stock').fetchall())]
 finally:con.close()
