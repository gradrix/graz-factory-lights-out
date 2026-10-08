import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'distance', 'grid': ['...', '##.', '...'], 'start': [0, 0], 'end': [2, 0]}), 6)
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'distance', 'grid': ['.#.'], 'start': [0, 0], 'end': [0, 2]}), None)
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'distance', 'grid': ['.'], 'start': [0, 0], 'end': [0, 0]}), 0)
