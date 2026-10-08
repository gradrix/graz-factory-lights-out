import unittest
from api import dispatch


def put(key, weight, value=None):
    return {'op': 'put', 'key': key, 'value': value, 'weight': weight}


def cache(capacity, operations):
    return dispatch({'action': 'cache', 'capacity': capacity, 'operations': operations})


class CacheTests(unittest.TestCase):
    def test_evicts_least_recent_by_weight(self):
        result = cache(5, [put('a', 2), put('b', 2), {'op': 'get', 'key': 'a'}, put('c', 3)])
        self.assertEqual(result['results'][-1], {'stored': True, 'evicted': ['b']})
        self.assertEqual([e['key'] for e in result['entries']], ['a', 'c'])

    def test_oversized_put_leaves_cache(self):
        result = cache(3, [put('a', 1, 'old'), put('a', 4, 'new'), {'op': 'get', 'key': 'zz'}])
        self.assertEqual(result['results'][1:], [{'stored': False, 'evicted': []}, {'hit': False, 'value': None}])
        self.assertEqual(result['entries'], [{'key': 'a', 'value': 'old', 'weight': 1}])
        self.assertEqual(cache(0, []), {'results': [], 'entries': []})

    def test_rejects_invalid_capacity_or_weight(self):
        for capacity, operations in ((-1, []), (5, [put('a', 0)])):
            with self.assertRaises(ValueError):
                cache(capacity, operations)


if __name__ == '__main__':
    unittest.main()
