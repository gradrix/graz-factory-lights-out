import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'readiness', 'required': ['db'], 'checks': [{'service': 'db', 'state': 'up', 'critical': True}, {'service': 'web', 'state': 'up', 'critical': False}], 'quorum': 2}),{'ready': True, 'up': 2, 'blockers': []}))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'readiness', 'required': ['db', 'cache'], 'checks': [{'service': 'db', 'state': 'down', 'critical': False}, {'service': 'mail', 'state': 'unknown', 'critical': True}], 'quorum': 0}),{'ready': False, 'up': 0, 'blockers': ['cache', 'db', 'mail']}))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'readiness', 'required': [], 'checks': [{'service': 'x', 'state': 'down', 'critical': True}, {'service': 'x', 'state': 'unknown', 'critical': False}], 'quorum': 0}),{'ready': True, 'up': 0, 'blockers': []}))
