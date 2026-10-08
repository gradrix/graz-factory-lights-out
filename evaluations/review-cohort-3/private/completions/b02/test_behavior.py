import unittest
from api import dispatch


def admit(history, now, window, limit):
    return dispatch({'action': 'admit', 'history': history, 'now': now, 'window': window, 'limit': limit})


class AdmitTests(unittest.TestCase):
    def test_admits_and_appends_now(self):
        self.assertEqual(admit([0, 5, 5], 10, 10, 3), {'allowed': True, 'history': [5, 5, 10], 'retry_at': None})

    def test_left_boundary_is_excluded(self):
        self.assertEqual(admit([0], 10, 10, 1), {'allowed': True, 'history': [10], 'retry_at': None})

    def test_denied_reports_retry_time(self):
        self.assertEqual(admit([5, 5], 10, 10, 2), {'allowed': False, 'history': [5, 5], 'retry_at': 15})
        self.assertEqual(admit([1, 2, 3, 4], 5, 10, 2), {'allowed': False, 'history': [1, 2, 3, 4], 'retry_at': 13})

    def test_zero_limit_has_no_retry(self):
        self.assertEqual(admit([], 3, 5, 0), {'allowed': False, 'history': [], 'retry_at': None})

    def test_rejects_invalid_input(self):
        for args in (([2, 1], 2, 1, 1), ([3], 2, 1, 1), ([], 0, 0, 1), ([], 0, 1, -1)):
            with self.assertRaises(ValueError):
                admit(*args)


if __name__ == '__main__':
    unittest.main()
