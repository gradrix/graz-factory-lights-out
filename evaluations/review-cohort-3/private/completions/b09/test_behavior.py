import unittest
from api import dispatch


def migrate(document):
    return dispatch({'action': 'migrate', 'document': document})


EXPECTED = {'revision': 3, 'title': 'T', 'accounts': {'u2': {'profile': {'name': 'Bé'}, 'enabled': False},
                                                       'u1': {'profile': {'name': 'A'}, 'enabled': True}},
            'order': ['u2', 'u1']}


class MigrateTests(unittest.TestCase):
    def test_revision_one(self):
        doc = {'revision': 1, 'title': 'T', 'users': [{'id': 'u2', 'name': 'Bé', 'active': False},
                                                       {'id': 'u1', 'name': 'A', 'active': True}]}
        self.assertEqual(migrate(doc), EXPECTED)

    def test_revision_two_and_idempotence(self):
        doc = {'revision': 2, 'title': 'T', 'users': [{'id': 'u2', 'profile': {'name': 'Bé'}, 'enabled': False},
                                                       {'id': 'u1', 'profile': {'name': 'A'}, 'enabled': True}]}
        self.assertEqual(migrate(doc), EXPECTED)
        self.assertEqual(migrate(EXPECTED), EXPECTED)
        self.assertEqual(migrate({'revision': 1, 'users': []}), {'revision': 3, 'accounts': {}, 'order': []})

    def test_rejects_unknown_revision_and_duplicates(self):
        for doc in ({'revision': 4}, {'revision': 1, 'users': [{'id': 'a', 'name': 'x', 'active': True}] * 2}):
            with self.assertRaises(ValueError):
                migrate(doc)


if __name__ == '__main__':
    unittest.main()
