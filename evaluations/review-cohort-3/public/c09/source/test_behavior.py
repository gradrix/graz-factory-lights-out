import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'seconds', 'text': '1h2m3s'}), 3723)
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'seconds', 'text': '90m'}), 5400)
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'seconds', 'text': '000s'}), 0)
 def test_case_3(self):
  self.assertEqual(dispatch({'action': 'seconds', 'text': '2h4s'}), 7204)
