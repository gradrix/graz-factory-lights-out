import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'encode', 'values': [1, 1, 2, 1, 1]}), [[1, 2], [2, 1], [1, 2]])
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'encode', 'values': []}), [])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'decode', 'runs': [[1, 2], [1, 1], [-2, 2]]}), [1, 1, 1, -2, -2])
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'decode', 'runs': [[1, 0]]})
