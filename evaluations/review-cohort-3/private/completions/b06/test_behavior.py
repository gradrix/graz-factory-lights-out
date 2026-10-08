import unittest
from api import dispatch


def validate(entries, max_total):
    return dispatch({'action': 'validate', 'entries': entries, 'max_total': max_total})


class ValidateTests(unittest.TestCase):
    def test_normalizes_and_sorts(self):
        result = validate([{'path': './b//x', 'size': 3}, {'path': 'a', 'size': 1}], 10)
        self.assertEqual(result, {'files': [{'path': 'a', 'size': 1}, {'path': 'b/x', 'size': 3}], 'total': 4})

    def test_total_equal_to_limit_is_allowed(self):
        self.assertEqual(validate([{'path': 'a', 'size': 2}, {'path': 'b', 'size': 3}], 5)['total'], 5)
        self.assertEqual(validate([], 0), {'files': [], 'total': 0})

    def test_rejects_unsafe_paths_and_conflicts(self):
        for path in ('', '/etc', '../x', 'a/../b', 'a\\b', 'C:x', 'x\x00y', '.'):
            with self.assertRaises(ValueError):
                validate([{'path': path, 'size': 1}], 10)
        for entries in ([{'path': 'a//b', 'size': 1}, {'path': 'a/./b', 'size': 1}],
                        [{'path': 'a/b', 'size': 1}, {'path': 'a', 'size': 1}]):
            with self.assertRaises(ValueError):
                validate(entries, 10)

    def test_rejects_sizes_over_limit(self):
        with self.assertRaises(ValueError):
            validate([{'path': 'a', 'size': 2}], 1)
        with self.assertRaises(ValueError):
            validate([{'path': 'a', 'size': -1}], 1)


if __name__ == '__main__':
    unittest.main()
