import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'pack', 'fields': [{'width': 3, 'value': 5}, {'width': 4, 'value': 2}]}), {'value': 82, 'bits': 7})
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'unpack', 'widths': [3, 4], 'value': 82}), [5, 2])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'pack', 'fields': []}), {'value': 0, 'bits': 0})
 def test_rejected(self):
  with self.assertRaises(OverflowError):dispatch({'action': 'pack', 'fields': [{'width': 2, 'value': 4}]})
