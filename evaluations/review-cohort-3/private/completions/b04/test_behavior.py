import unittest
from api import dispatch


def resolve(defaults, layers, required=()):
    return dispatch({'action': 'resolve', 'defaults': defaults, 'layers': layers, 'required': list(required)})


class ResolveTests(unittest.TestCase):
    def test_layers_merge_in_order(self):
        result = resolve({'a': 1, 'n': {'x': 1, 'y': 2}, 'l': [1], 'z': None},
                         [{'n': {'x': None, 'q': 3}, 'l': [2]}, {'a': 4, 'n': {'y': 5}}], ['z'])
        self.assertEqual(result, {'a': 4, 'n': {'y': 5, 'q': 3}, 'l': [2], 'z': None})

    def test_new_objects_apply_nested_deletions(self):
        self.assertEqual(resolve({'n': 1}, [{'n': {'ghost': None, 'x': 2}}]), {'n': {'x': 2}})
        self.assertEqual(resolve({}, [{'absent': None}, {'new': {'gone': None}}]), {'new': {}})

    def test_missing_required_key(self):
        with self.assertRaises(ValueError):
            resolve({'a': 1}, [{'a': None}], ['a'])


if __name__ == '__main__':
    unittest.main()
