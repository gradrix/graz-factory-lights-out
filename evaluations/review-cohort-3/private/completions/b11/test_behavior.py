import unittest
from api import dispatch


def event(source, seq, data=None):
    return {'source': source, 'seq': seq, 'data': data}


def ingest(watermarks, events):
    return dispatch({'action': 'ingest', 'watermarks': watermarks, 'events': events})


class IngestTests(unittest.TestCase):
    def test_releases_contiguous_events(self):
        result = ingest({'a': 1, 'idle': 9}, [event('a', 4), event('b', 2), event('a', 2), event('b', 1), event('a', 2)])
        self.assertEqual(result, {'watermarks': {'a': 2, 'idle': 9, 'b': 2},
                                  'released': [event('a', 2), event('b', 1), event('b', 2)],
                                  'pending': [event('a', 4)]})

    def test_gap_keeps_events_pending(self):
        self.assertEqual(ingest({}, [event('z', 3)]), {'watermarks': {'z': 0}, 'released': [], 'pending': [event('z', 3)]})
        self.assertEqual(ingest({}, []), {'watermarks': {}, 'released': [], 'pending': []})

    def test_rejects_conflicting_data(self):
        with self.assertRaises(ValueError):
            ingest({}, [event('a', 2, 1), event('a', 2, 2)])


if __name__ == '__main__':
    unittest.main()
