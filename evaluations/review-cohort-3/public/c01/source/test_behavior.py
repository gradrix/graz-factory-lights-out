import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'allocate', 'weights': [1, 1, 1], 'seats': 2}), [1, 1, 0])
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'allocate', 'weights': [5, 3, 2], 'seats': 7}), [4, 2, 1])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'allocate', 'weights': [0, 9, 1], 'seats': 1}), [0, 1, 0])
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'allocate', 'weights': [0, 0], 'seats': 2})
