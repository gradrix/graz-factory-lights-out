import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'render', 'template': 'host=${HOST}\nport=${PORT}', 'variables': {'HOST': 'example', 'PORT': '443'}}),'host=example\nport=443'))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'render', 'template': '$${X}:$$:${X}', 'variables': {'X': '${Y}'}}),'${X}:$:${Y}'))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'render', 'template': '', 'variables': {}}),''))
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'render', 'template': '$', 'variables': {}})
