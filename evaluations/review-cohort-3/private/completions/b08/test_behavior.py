import unittest
from api import dispatch


def group(requested, responses):
    return dispatch({'action': 'group', 'requested': requested, 'responses': responses})


class GroupTests(unittest.TestCase):
    def test_requested_order_wins(self):
        responses = [{'id': 'c', 'ok': False, 'error': 'boom'}, {'id': 'a', 'ok': True, 'value': 1}]
        self.assertEqual(group(['a', 'b', 'c'], responses),
                         {'successes': [{'id': 'a', 'value': 1}], 'failures': [{'id': 'c', 'error': 'boom'}], 'missing': ['b']})

    def test_falsey_values_are_successes(self):
        values = [None, False, 0, '']
        ids = ['n', 'f', 'z', 'e']
        responses = [{'id': i, 'ok': True, 'value': v} for i, v in zip(ids, values)]
        result = group(ids, list(reversed(responses)))
        self.assertEqual(result['successes'], [{'id': i, 'value': v} for i, v in zip(ids, values)])
        self.assertEqual(group([], []), {'successes': [], 'failures': [], 'missing': []})

    def test_rejects_bad_ids(self):
        ok = {'id': 'a', 'ok': True, 'value': 1}
        for requested, responses in ((['a', 'a'], []), (['a'], [dict(ok, id='x')]), (['a'], [ok, ok])):
            with self.assertRaises(ValueError):
                group(requested, responses)


if __name__ == '__main__':
    unittest.main()
