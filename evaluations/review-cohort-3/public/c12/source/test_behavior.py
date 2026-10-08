import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'parse', 'query': 'a=1&a=2&empty&=x&&'}), [['a', '1'], ['a', '2'], ['empty', ''], ['', 'x']])
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'parse', 'query': 'x=a%26b%3Dc&%C3%A9=hello+world'}), [['x', 'a&b=c'], ['é', 'hello world']])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'parse', 'query': 'a=b=c'}), [['a', 'b=c']])
 def test_rejected(self):
  with self.assertRaises(ValueError):dispatch({'action': 'parse', 'query': 'a=%'})
