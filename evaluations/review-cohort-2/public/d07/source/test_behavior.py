import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 105, 'tolerance': 5, 'signature': 'sha256=b6ae95232f7a6f10ed56c0c2931bda6344efb9e66d09bf79943ca1df746bbddf'}),True))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'verify', 'secret': 'é', 'body': '猫\n', 'timestamp': 0, 'now': 0, 'tolerance': 0, 'signature': 'sha256=6745333ad1bd28156fb8fe5136e126b0af176a14850bcd743711191fec27c7e4'}),True))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'verify', 'secret': 'key', 'body': '{}', 'timestamp': 100, 'now': 94, 'tolerance': 5, 'signature': 'sha256=b6ae95232f7a6f10ed56c0c2931bda6344efb9e66d09bf79943ca1df746bbddf'}),False))
