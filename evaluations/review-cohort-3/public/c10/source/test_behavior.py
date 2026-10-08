import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'tally', 'candidates': ['b', 'a', 'c'], 'ballots': [['a', 'a'], ['b'], []]}), [{'candidate': 'b', 'votes': 1}, {'candidate': 'a', 'votes': 1}, {'candidate': 'c', 'votes': 0}])
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'tally', 'candidates': [], 'ballots': [[]]}), [])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'tally', 'candidates': ['x', 'y'], 'ballots': [['y'], ['y'], ['x']]}), [{'candidate': 'y', 'votes': 2}, {'candidate': 'x', 'votes': 1}])
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'tally', 'candidates': ['a'], 'ballots': [['a'], ['z']]})
