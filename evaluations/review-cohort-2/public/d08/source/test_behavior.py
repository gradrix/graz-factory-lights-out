import unittest
from api import dispatch
def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
class BehaviorTests(unittest.TestCase):
 def test_case_0(self):
  self.assertTrue(json_equal(dispatch({'action': 'headings', 'markdown': '# Hello World\ntext\n## Hello World\n'}),[{'level': 1, 'text': 'Hello World', 'line': 1, 'anchor': 'hello-world'}, {'level': 2, 'text': 'Hello World', 'line': 3, 'anchor': 'hello-world-2'}]))
 def test_case_1(self):
  self.assertTrue(json_equal(dispatch({'action': 'headings', 'markdown': '```python\n# hidden\n```\n # indented\n####### too deep\n#No space\n# !!!'}),[{'level': 1, 'text': '!!!', 'line': 7, 'anchor': 'section'}]))
 def test_case_2(self):
  self.assertTrue(json_equal(dispatch({'action': 'headings', 'markdown': '# A\n# A-2\n# A\n# Café --- X'}),[{'level': 1, 'text': 'A', 'line': 1, 'anchor': 'a'}, {'level': 1, 'text': 'A-2', 'line': 2, 'anchor': 'a-2'}, {'level': 1, 'text': 'A', 'line': 3, 'anchor': 'a-3'}, {'level': 1, 'text': 'Café --- X', 'line': 4, 'anchor': 'caf-x'}]))
