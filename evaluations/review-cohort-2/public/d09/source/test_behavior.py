import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'export', 'invoices': [{'id': 'a', 'customer': 'Ada', 'items': [{'quantity': 3, 'unit_cents': 105}, {'quantity': 0, 'unit_cents': 1}]}]}),'id,customer,total\r\na,Ada,3.15\r\n'))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'export', 'invoices': [{'id': 'a,1', 'customer': '"X"\nY', 'items': []}]}),'id,customer,total\r\n"a,1","""X""\nY",0.00\r\n'))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'export', 'invoices': []}),'id,customer,total\r\n'))
