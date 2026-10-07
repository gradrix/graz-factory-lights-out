import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'plan', 'backups': [{'id': 'old', 'service': 'db', 'finished': '2026-01-01T10:00:00Z'}, {'id': 'early', 'service': 'db', 'finished': '2026-01-02T10:00:00Z'}, {'id': 'late', 'service': 'db', 'finished': '2026-01-02T11:00:00Z'}, {'id': 'web', 'service': 'web', 'finished': '2025-12-01T00:00:00Z'}], 'days': 1}),{'keep': ['late', 'web'], 'delete': ['old', 'early']}))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'plan', 'backups': [{'id': 'z', 'service': 'x', 'finished': '2026-01-01T00:00:00Z'}, {'id': 'a', 'service': 'x', 'finished': '2026-01-01T00:00:00Z'}], 'days': 3}),{'keep': ['a'], 'delete': ['z']}))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'plan', 'backups': [], 'days': 0}),{'keep': [], 'delete': []}))
