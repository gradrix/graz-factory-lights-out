import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'digest', 'changes': [{'id': '1', 'category': 'fixed', 'title': ' A\n fix ', 'internal': False}, {'id': '2', 'category': 'added', 'title': 'New **API**', 'internal': False}]}),'## Added\n- New **API**\n\n## Fixed\n- A fix\n'))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'digest', 'changes': [{'id': 'x', 'category': 'added', 'title': 'Old', 'internal': False}, {'id': 'y', 'category': 'added', 'title': 'Y', 'internal': False}, {'id': 'x', 'category': 'fixed', 'title': 'Secret', 'internal': True}]}),'## Added\n- Y\n'))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'digest', 'changes': []}),''))
