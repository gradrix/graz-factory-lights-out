import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'select', 'artifacts': [{'id': 'a', 'platform': 'linux', 'version': '1.9.9', 'yanked': False}, {'id': 'b', 'platform': 'linux', 'version': '1.10.0', 'yanked': False}, {'id': 'c', 'platform': 'linux', 'version': '2.0.0', 'yanked': False}], 'platform': 'linux', 'major': 1}),{'id': 'b', 'version': '1.10.0'}))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'select', 'artifacts': [{'id': 'z', 'platform': 'x', 'version': '0.1.0', 'yanked': False}, {'id': 'a', 'platform': 'x', 'version': '0.1.0', 'yanked': False}, {'id': 'y', 'platform': 'x', 'version': '0.2.0', 'yanked': True}], 'platform': 'x', 'major': 0}),{'id': 'a', 'version': '0.1.0'}))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'select', 'artifacts': [], 'platform': 'x', 'major': 1}),None))
