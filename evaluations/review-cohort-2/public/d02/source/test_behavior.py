import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'report', 'entries': [{'route': '/b', 'status': 503, 'ms': 90}, {'route': '/a', 'status': 404, 'ms': 0}, {'route': '/b', 'status': 200, 'ms': 10}], 'min_requests': 1}),[{'route': '/a', 'requests': 1, 'errors': 0, 'p95_ms': 0}, {'route': '/b', 'requests': 2, 'errors': 1, 'p95_ms': 90}]))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'report', 'entries': [{'route': '/x', 'status': 200, 'ms': 1}, {'route': '/x', 'status': 200, 'ms': 2}, {'route': '/x', 'status': 200, 'ms': 3}, {'route': '/x', 'status': 200, 'ms': 4}, {'route': '/x', 'status': 200, 'ms': 5}, {'route': '/x', 'status': 200, 'ms': 6}, {'route': '/x', 'status': 200, 'ms': 7}, {'route': '/x', 'status': 200, 'ms': 8}, {'route': '/x', 'status': 200, 'ms': 9}, {'route': '/x', 'status': 200, 'ms': 10}, {'route': '/x', 'status': 200, 'ms': 11}, {'route': '/x', 'status': 200, 'ms': 12}, {'route': '/x', 'status': 200, 'ms': 13}, {'route': '/x', 'status': 200, 'ms': 14}, {'route': '/x', 'status': 200, 'ms': 15}, {'route': '/x', 'status': 200, 'ms': 16}, {'route': '/x', 'status': 200, 'ms': 17}, {'route': '/x', 'status': 200, 'ms': 18}, {'route': '/x', 'status': 200, 'ms': 19}, {'route': '/x', 'status': 200, 'ms': 20}], 'min_requests': 20}),[{'route': '/x', 'requests': 20, 'errors': 0, 'p95_ms': 19}]))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'report', 'entries': [], 'min_requests': 1}),[]))
