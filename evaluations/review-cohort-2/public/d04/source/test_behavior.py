import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def prepare(self,p):
  import tempfile,sqlite3,copy,pathlib
  p=copy.deepcopy(p)
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);p['db']=str(pathlib.Path(tmp.name)/'stock.db')
  with sqlite3.connect(p['db']) as con:
   con.execute('CREATE TABLE stock(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL)')
   con.executemany('INSERT INTO stock VALUES (?,?)',[('a',5),('b',2)])
  return p
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch(self.prepare({'action': 'adjust', 'changes': [{'sku': 'a', 'delta': -2}, {'sku': 'b', 'delta': 3}]})),[{'sku': 'a', 'quantity': 3}, {'sku': 'b', 'quantity': 5}]))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch(self.prepare({'action': 'adjust', 'changes': [{'sku': 'a', 'delta': -5}, {'sku': 'a', 'delta': 2}]})),[{'sku': 'a', 'quantity': 2}, {'sku': 'b', 'quantity': 2}]))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch(self.prepare({'action': 'adjust', 'changes': []})),[{'sku': 'a', 'quantity': 5}, {'sku': 'b', 'quantity': 2}]))
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch(self.prepare({'action': 'adjust', 'changes': [{'sku': 'a', 'delta': -1}, {'sku': 'missing', 'delta': 1}]}))
