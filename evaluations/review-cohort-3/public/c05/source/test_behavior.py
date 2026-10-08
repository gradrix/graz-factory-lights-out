import unittest
from api import dispatch
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertEqual(dispatch({'action': 'wrap', 'text': 'one two three', 'width': 7}), ['one two', 'three'])
 def test_case_1(self):
  self.assertEqual(dispatch({'action': 'wrap', 'text': '\na  b\n', 'width': 2}), ['', 'a', 'b', ''])
 def test_case_2(self):
  self.assertEqual(dispatch({'action': 'wrap', 'text': 'abcdef x y', 'width': 3}), ['abcdef', 'x y'])
