import unittest
from api import dispatch


def node(key, *deps):
    return {'id': key, 'deps': list(deps)}


class OrderTests(unittest.TestCase):
    def test_dependency_comes_first(self):
        nodes = [node('app', 'lib'), node('lib')]
        self.assertEqual(dispatch({'action': 'order', 'nodes': nodes}), ['lib', 'app'])

    def test_chain_and_repeated_dependency(self):
        nodes = [node('c', 'b', 'b'), node('b', 'a'), node('a')]
        self.assertEqual(dispatch({'action': 'order', 'nodes': nodes}), ['a', 'b', 'c'])

    def test_empty_nodes(self):
        self.assertEqual(dispatch({'action': 'order', 'nodes': []}), [])

    def test_rejects_cycle_unknown_and_duplicate(self):
        for nodes in ([node('a', 'a')], [node('a', 'b'), node('b', 'a')], [node('a', 'zzz')], [node('a'), node('a')]):
            with self.assertRaises(ValueError):
                dispatch({'action': 'order', 'nodes': nodes})

    def test_labels_unchanged(self):
        self.assertEqual(dispatch({'action': 'labels', 'nodes': [{'id': 'b'}, {'id': 'a'}]}), ['b', 'a'])


if __name__ == '__main__':
    unittest.main()
