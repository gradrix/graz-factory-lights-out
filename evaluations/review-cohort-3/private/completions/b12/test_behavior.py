import unittest
from api import dispatch


def index(text, offsets):
    return dispatch({'action': 'index', 'text': text, 'byte_offsets': offsets})


class IndexTests(unittest.TestCase):
    def test_multibyte_boundaries(self):
        self.assertEqual(index('aé猫😀', [0, 3, 10, 3]),
                         {'byte_length': 10, 'char_to_byte': [0, 1, 3, 6, 10], 'byte_to_char': [0, 2, 4, 2]})

    def test_empty_text(self):
        self.assertEqual(index('', [0]), {'byte_length': 0, 'char_to_byte': [0], 'byte_to_char': [0]})

    def test_rejects_invalid_offsets(self):
        for offset in (-1, 2, 11):
            with self.assertRaises(ValueError):
                index('aé猫😀', [offset])


if __name__ == '__main__':
    unittest.main()
