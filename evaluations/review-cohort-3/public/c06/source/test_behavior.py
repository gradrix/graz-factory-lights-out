import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'check', 'number': '7992 7398-713'}), True)
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'check', 'number': '79927398714'}), False)
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'append', 'number': '7992739871'}), '79927398713')
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'append', 'number': ' - '})
