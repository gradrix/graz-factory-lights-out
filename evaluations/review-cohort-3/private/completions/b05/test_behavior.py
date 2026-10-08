import unittest
from api import dispatch


class LogFieldTests(unittest.TestCase):
    def test_encode_sorts_and_escapes(self):
        fields = {'b': 'x=y\té', 'a': 'back\\slash\nline\r'}
        line = dispatch({'action': 'encode', 'fields': fields})
        self.assertEqual(line, 'a=back\\\\slash\\nline\\r\tb=x=y\\té')
        self.assertEqual(dispatch({'action': 'decode', 'line': line}), fields)

    def test_empty_values(self):
        self.assertEqual(dispatch({'action': 'encode', 'fields': {}}), '')
        self.assertEqual(dispatch({'action': 'decode', 'line': ''}), {})
        self.assertEqual(dispatch({'action': 'decode', 'line': 'k=a=b\tv='}), {'k': 'a=b', 'v': ''})

    def test_rejects_malformed(self):
        for line in ('a=1\t', 'novalue', 'a=\\x', 'a=\\', 'a=1\ta=2', '1a=x'):
            with self.assertRaises(ValueError):
                dispatch({'action': 'decode', 'line': line})
        with self.assertRaises(ValueError):
            dispatch({'action': 'encode', 'fields': {'bad-key': 'x'}})


if __name__ == '__main__':
    unittest.main()
