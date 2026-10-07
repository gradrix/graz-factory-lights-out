import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'import_contacts', 'csv': 'email,name\n A@X , Ada \na@x,Ignored\nb@x,"Bee, Two"\n', 'existing': []}),{'added': [{'email': 'a@x', 'name': 'Ada'}, {'email': 'b@x', 'name': 'Bee, Two'}], 'skipped': 1}))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'import_contacts', 'csv': 'email,name\na@x,A\nc@x,C\na@x,A2\n', 'existing': [{'email': 'a@x', 'name': 'Old'}]}),{'added': [{'email': 'c@x', 'name': 'C'}], 'skipped': 2}))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'import_contacts', 'csv': 'email,name\n', 'existing': []}),{'added': [], 'skipped': 0}))
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'import_contacts', 'csv': '', 'existing': []})
