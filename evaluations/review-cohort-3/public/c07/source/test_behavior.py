import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'occurrences', 'start': '2024-01-31', 'day': 31, 'count': 3}), ['2024-01-31', '2024-02-29', '2024-03-31'])
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'occurrences', 'start': '2023-02-28', 'day': 31, 'count': 2}), ['2023-02-28', '2023-03-31'])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'occurrences', 'start': '2024-12-20', 'day': 10, 'count': 2}), ['2025-01-10', '2025-02-10'])
