import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'match', 'choices': [['a', 'b'], ['a']]}), 2)
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'match', 'choices': [['a'], ['a'], []]}), 1)
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'match', 'choices': []}), 0)
