import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'redact', 'document': {'Token': 's', 'nested': [{'token': {'a': 1}, 'keep': False}, True]}, 'keys': ['TOKEN'], 'replacement': '***'}),{'Token': '***', 'nested': [{'token': '***', 'keep': False}, True]}))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'redact', 'document': {'STRASSE': 'secret', ' token ': 'keep'}, 'keys': ['straße', 'token'], 'replacement': None}),{'STRASSE': None, ' token ': 'keep'}))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'redact', 'document': [1, True, None], 'keys': [], 'replacement': 0}),[1, True, None]))
