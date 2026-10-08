import unittest
from api import dispatch


def schedule(**changes):
    payload = {'action': 'schedule', 'now': 100, 'attempt': 1, 'base': 3, 'cap': 10,
               'max_attempts': 8, 'outcome': 'transient'}
    payload.update(changes)
    return dispatch(payload)


class ScheduleTests(unittest.TestCase):
    def test_exponential_delay(self):
        self.assertEqual(schedule(), {'retry': True, 'at': 103, 'delay': 3})
        self.assertEqual(schedule(attempt=2), {'retry': True, 'at': 106, 'delay': 6})

    def test_cap_and_retry_after(self):
        self.assertEqual(schedule(attempt=5)['delay'], 10)
        self.assertEqual(schedule(retry_after=50), {'retry': True, 'at': 150, 'delay': 50})
        self.assertEqual(schedule(retry_after=None)['delay'], 3)

    def test_no_retry_cases(self):
        for changes in ({'outcome': 'success'}, {'outcome': 'permanent'}, {'attempt': 8}):
            self.assertEqual(schedule(**changes), {'retry': False, 'at': None, 'delay': None})

    def test_rejects_invalid_values(self):
        for changes in ({'base': 0}, {'attempt': 0}, {'cap': 0}, {'max_attempts': 0},
                        {'retry_after': -1}, {'outcome': 'other'}, {'outcome': 'success', 'base': 0}):
            with self.assertRaises(ValueError):
                schedule(**changes)


if __name__ == '__main__':
    unittest.main()
