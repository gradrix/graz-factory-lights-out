import unittest
from api import dispatch


def update(records, key, expected, patch):
    return dispatch({'action': 'update', 'records': records, 'id': key, 'expected': expected, 'patch': patch})


class UpdateTests(unittest.TestCase):
    def test_create_when_absent(self):
        result = update({}, 'r', None, {'name': 'x'})
        self.assertEqual(result, {'applied': True, 'records': {'r': {'version': 1, 'data': {'name': 'x'}}},
                                  'record': {'version': 1, 'data': {'name': 'x'}}})

    def test_matching_version_merges_and_keeps_nulls(self):
        records = {'r': {'version': 4, 'data': {'a': 1, 'b': 2}}}
        result = update(records, 'r', 4, {'b': None, 'c': 3})
        self.assertTrue(result['applied'])
        self.assertEqual(result['record'], {'version': 5, 'data': {'a': 1, 'b': None, 'c': 3}})

    def test_conflicts_leave_records_unchanged(self):
        records = {'r': {'version': 0, 'data': {}}}
        for expected in (None, 1):
            result = update(records, 'r', expected, {'x': 1})
            self.assertEqual(result, {'applied': False, 'records': records, 'record': records['r']})
        self.assertEqual(update({}, 'missing', 0, {}), {'applied': False, 'records': {}, 'record': None})

    def test_results_are_independent(self):
        result = update({}, 'r', None, {'list': [1]})
        result['record']['data']['list'].append(2)
        self.assertEqual(result['records']['r']['data']['list'], [1])


if __name__ == '__main__':
    unittest.main()
