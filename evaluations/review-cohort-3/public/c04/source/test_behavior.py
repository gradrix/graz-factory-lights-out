import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'evaluate', 'coefficients': [2, 3, 4], 'x': 2}), {'value': 24, 'derivative': 19})
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'evaluate', 'coefficients': [], 'x': 0}), {'value': 0, 'derivative': 0})
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'evaluate', 'coefficients': [7], 'x': -5}), {'value': 7, 'derivative': 0})
